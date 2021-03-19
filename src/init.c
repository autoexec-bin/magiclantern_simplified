/** \file
 * Common startup code (for all models).
 *
 * !!!!!! FOR NEW PORTS, READ PROPERTY.C FIRST !!!!!!
 * OTHERWISE YOU CAN CAUSE PERMANENT CAMERA DAMAGE
 * 
 */
/*
 * Copyright (C) 2009 Trammell Hudson <hudson+ml@osresearch.net>
 * 
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the
 * Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor,
 * Boston, MA  02110-1301, USA.
 */

#include "dryos.h"
#include "config.h"
#include "version.h"
#include "bmp.h"
#include "menu.h"
#include "property.h"
#include "consts.h"
#include "tskmon.h"

#include "boot-hack.h"
#include "ml-cbr.h"
#include "backtrace.h"


#if defined(FEATURE_GPS_TWEAKS)
#include "gps.h"
#endif

#if defined(CONFIG_HELLO_WORLD)
#include "fw-signature.h"
#endif

static int _hold_your_horses = 1; // 0 after config is read
int ml_started = 0; // 1 after ML is fully loaded
int ml_gui_initialized = 0; // 1 after gui_main_task is started 


/**
 * Called by DryOS when it is dispatching (or creating?)
 * a new task.
 */
static void
my_task_dispatch_hook(
        struct context ** p_context_old,    /* on new DryOS (6D+), this argument is different (small number, unknown meaning) */
        struct task * prev_task_unused,     /* only present on new DryOS */
        struct task * next_task_new         /* only present on new DryOS; old versions use HIJACK_TASK_ADDR */
)
{
    struct task * next_task =  next_task_new;

    if (!next_task)
        return;

    struct context * context = next_task->context;
    // Do nothing unless a new task is starting via the trampoile
    if( context->pc != (uint32_t) task_trampoline )
        return;

    thunk entry = (thunk) next_task->entry;
    

    extern struct task_mapping _task_overrides_start[];
    extern struct task_mapping _task_overrides_end[];
    struct task_mapping * mapping = _task_overrides_start;
    
    qprintf("[****] Starting task %x(%x) %s\n", next_task->entry, next_task->arg, next_task->name);

    for( ; mapping < _task_overrides_end ; mapping++ )
    {
        thunk original_entry = mapping->orig;
        if( original_entry != entry )
            continue;

/* -- can't call debugmsg from this context */
        qprintf("[****] Replacing task %x with %x\n",
            original_entry,
            mapping->replacement
        );

        next_task->entry = mapping->replacement;
        break;
    }
}

//TASK_OVERRIDE( gui_main_task, kitor_gui_main_task);


/** Call all of the init functions  */
static void
call_init_funcs()
{
    extern struct task_create _init_funcs_start[];
    extern struct task_create _init_funcs_end[];
    struct task_create * init_func = _init_funcs_start;

    for( ; init_func < _init_funcs_end ; init_func++ )
    {
#if defined(POSITION_INDEPENDENT)
        init_func->entry = PIC_RESOLVE(init_func->entry);
        init_func->name = PIC_RESOLVE(init_func->name);
#endif
        /*DebugMsg( DM_MAGIC, 3,
            "Calling init_func %s (%x)",
            init_func->name,
            (uint32_t) init_func->entry
        ); */
        
        uart_printf("\nCalling init_func %s (%x)\n",
            init_func->name,
            (uint32_t) init_func->entry
        );  
        thunk entry = (thunk) init_func->entry;
        entry();
    }
}

static void nop( void ) { }
void menu_init( void ) __attribute__((weak,alias("nop")));
void debug_init( void ) __attribute__((weak,alias("nop")));

static int magic_off = 0; // Set to 1 to disable ML
static int magic_off_request = 0;

int magic_is_off() 
{
    return magic_off; 
}

void _disable_ml_startup() {
    magic_off_request = 1;
}

#if defined(CONFIG_AUTOBACKUP_ROM)

#define BACKUP_BLOCKSIZE 0x00100000

static void backup_region(char *file, uint32_t base, uint32_t length)
{
    FILE *handle = NULL;
    uint32_t size = 0;
    uint32_t pos = 0;
    
    /* already backed up that region? */
    if((FIO_GetFileSize( file, &size ) == 0) && (size == length) )
    {
        return;
    }
    
    /* no, create file and store data */

    void* buf = malloc(BACKUP_BLOCKSIZE);
    if (!buf) return;

    handle = FIO_CreateFile(file);
    if (handle)
    {
      while(pos < length)
      {
         uint32_t blocksize = BACKUP_BLOCKSIZE;
        
          if(length - pos < blocksize)
          {
              blocksize = length - pos;
          }
          
          /* copy to RAM before saving, because ROM is slow and may interfere with LiveView */
          memcpy(buf, &((uint8_t*)base)[pos], blocksize);
          
          FIO_WriteFile(handle, buf, blocksize);
          pos += blocksize;
      }
      FIO_CloseFile(handle);
    }
    
    free(buf);
}

static void backup_rom_task()
{
    backup_region("ML/LOGS/ROM1.BIN", 0xF8000000, 0x01000000);
    backup_region("ML/LOGS/ROM0.BIN", 0xF0000000, 0x01000000);
}
#endif

#ifdef CONFIG_HELLO_WORLD
static void hello_world()
{

    int sig = compute_signature((uint32_t*)SIG_START, 0x10000);
    while(1)
    {
        bmp_printf(FONT_LARGE, 50, 50, "Hello, World!");
        bmp_printf(FONT_LARGE, 50, 400, "firmware signature = 0x%x", sig);
        info_led_blink(1, 500, 500);
    }
}
#endif

#ifdef CONFIG_DUMPER_BOOTFLAG
static void dumper_bootflag()
{
    msleep(5000);
    SetGUIRequestMode(GUIMODE_PLAY);
    msleep(1000);
    bmp_fill(COLOR_BLACK, 0, 0, 720, 480);
    bmp_printf(FONT_LARGE, 50, 100, "Please wait...");
    msleep(2000);

    if (CURRENT_GUI_MODE != GUIMODE_PLAY)
    {
        bmp_printf(FONT_LARGE, 50, 150, "Hudson, we have a problem!");
        return;
    }
    
    /* this requires CONFIG_AUTOBACKUP_ROM */
    bmp_printf(FONT_LARGE, 50, 150, "ROM Backup...");
    backup_rom_task();

    // do not try to enable bootflag in LiveView, or during sensor cleaning (it will fail while writing to ROM)
    // no check is done here, other than a large delay and doing this while in Canon menu
    // todo: check whether the issue is still present with interrupts disabled
    bmp_printf(FONT_LARGE, 50, 200, "EnableBootDisk...");
    uint32_t old = cli();
    call("EnableBootDisk");
    sei(old);

    bmp_printf(FONT_LARGE, 50, 250, ":)");
}
#endif

static void led_fade(int arg1, void * on)
{
    /* emulate a fade-out PWM using a HPTimer */
    static int k = 16000;
    if (k > 0)
    {
        if (on) _card_led_on(); else _card_led_off();
        int next_delay = (on ? k : 16000 - k);   /* cycle: 16000 us => 62.5 Hz */
        SetHPTimerNextTick(arg1, next_delay, led_fade, led_fade, (void *) !on);
        k -= MAX(16, k/32);  /* adjust fading speed and shape here */
    }
}

/* This runs ML initialization routines and starts user tasks.
 * Unlike init_task, from here we can do file I/O and others.
 */
static void my_big_init_task()
{
    _mem_init();
    _find_ml_card();

    /* should we require SET for loading ML, or not? */
    extern int _set_at_startup;
    _set_at_startup = config_flag_file_setting_load("ML/SETTINGS/REQUIRE.SET");

    // at this point, gui_main_task should be started and should be able to tell whether SET was pressed at startup
    if (magic_off_request != _set_at_startup)
    {
        /* should we bypass loading ML? */
        /* (pressing SET after this point will be ignored) */
        magic_off = 1;

    #if !defined(CONFIG_NO_ADDITIONAL_VERSION)
        /* fixme: enable on all models */
        extern char additional_version[];
        additional_version[0] = '-';
        additional_version[1] = 'm';
        additional_version[2] = 'l';
        additional_version[3] = '-';
        additional_version[4] = 'o';
        additional_version[5] = 'f';
        additional_version[6] = 'f';
        additional_version[7] = '\0';
    #endif

        /* some very basic feedback - fade out the SD led */
        SetHPTimerAfterNow(1000, led_fade, led_fade, 0);

        /* do not continue loading ML */
        return;
    }

    _load_fonts();


#ifdef CONFIG_HELLO_WORLD
    hello_world();
    return;
#endif

#ifdef CONFIG_DUMPER_BOOTFLAG
    dumper_bootflag();
    return;
#endif
   
    call("DisablePowerSave");
    _ml_cbr_init();
    menu_init();
    debug_init();
    call_init_funcs();
    msleep(200); // leave some time for property handlers to run
    #if defined(CONFIG_AUTOBACKUP_ROM)
    /* backup ROM first time to be prepared if anything goes wrong. choose low prio */
    /* On 5D3, this needs to run after init functions (after card tests) */
    //task_create("ml_backup", 0x1f, 0x4000, backup_rom_task, 0 );
    #endif

    /* Read ML config. if feature disabled, nothing happens */
    config_load();

    debug_init_stuff();

    #ifdef FEATURE_GPS_TWEAKS
    gps_tweaks_startup_hook();
    #endif

    _hold_your_horses = 0; // config read, other overriden tasks may start doing their job

    // Create all of our auto-create tasks
    extern struct task_create _tasks_start[];
    extern struct task_create _tasks_end[];
    struct task_create * task = _tasks_start;

    int ml_tasks = 0;
    for( ; task < _tasks_end ; task++ )
    {
#if defined(POSITION_INDEPENDENT)
        task->name = PIC_RESOLVE(task->name);
        task->entry = PIC_RESOLVE(task->entry);
        task->arg = PIC_RESOLVE(task->arg);
#endif
        uart_printf("\nCalling task_create %s (%x)\n",
            task->name,
            (uint32_t) task->entry
        );  
        task_create(
            task->name,
            task->priority,
            task->stack_size,
            task->entry,
            task->arg
        );
        ml_tasks++;
    }
    
    msleep(500);
    ml_started = 1;
}

/** Blocks execution until config is read */
void hold_your_horses()
{
    while (_hold_your_horses)
    {
        msleep( 100 );
    }
}

/**
 * Custom assert handler - intercept ERR70 and try to save a crash log.
 * Crash log should contain Canon error message.
 */
static char assert_msg[512] = "";
static int (*old_assert_handler)(char*,char*,int,int) = 0;
const char* get_assert_msg() { return assert_msg; }

static int my_assert_handler(char* msg, char* file, int line, int arg4)
{
    uint32_t lr = read_lr();

    int len = snprintf(assert_msg, sizeof(assert_msg), 
        "ASSERT: %s\n"
        "at %s:%d, %s:%x\n"
        "lv:%d mode:%d\n\n", 
        msg, 
        file, line, get_current_task_name(), lr,
        lv, shooting_mode
    );
    backtrace_getstr(assert_msg + len, sizeof(assert_msg) - len);
    request_crash_log(1);
    return old_assert_handler(msg, file, line, arg4);
}

void ml_assert_handler(char* msg, char* file, int line, const char* func)
{
    int len = snprintf(assert_msg, sizeof(assert_msg), 
        "ML ASSERT:\n%s\n"
        "at %s:%d (%s), task %s\n"
        "lv:%d mode:%d\n\n", 
        msg, 
        file, line, func, get_current_task_name(), 
        lv, shooting_mode
    );
    backtrace_getstr(assert_msg + len, sizeof(assert_msg) - len);
    request_crash_log(2);
}

void ml_crash_message(char* msg)
{
    snprintf(assert_msg, sizeof(assert_msg), "%s", msg);
    request_crash_log(1);
}

/* called before Canon's init_task */
void boot_pre_init_task()
{
//#if !defined(CONFIG_HELLO_WORLD) && !defined(CONFIG_DUMPER_BOOTFLAG)
    // Install our task creation hooks
    qprint("[BOOT] installing task dispatch hook at "); qprintn((int)&task_dispatch_hook); qprint("\n");
    task_dispatch_hook = my_task_dispatch_hook;
    #ifdef CONFIG_TSKMON
    tskmon_init();
    #endif
//#endif
}

/* called right after Canon's init_task, while their initialization continues in background */
void boot_post_init_task(void)
{
#if defined(CONFIG_CRASH_LOG)
    // decompile TH_assert to find out the location
    old_assert_handler = (void*)MEM(DRYOS_ASSERT_HANDLER);
    *(void**)(DRYOS_ASSERT_HANDLER) = (void*)my_assert_handler;
#endif // (CONFIG_CRASH_LOG)

    DebugMsg( DM_MAGIC, 3, "Magic Lantern %s (%s)",
        build_version,
        build_id
    );

    DebugMsg( DM_MAGIC, 3, "Built on %s by %s",
        build_date,
        build_user
    );

#if !defined(CONFIG_NO_ADDITIONAL_VERSION)
    // Re-write the version string.
    // Don't use strcpy() so that this can be done
    // before strcpy() or memcpy() are located.
    extern char additional_version[];
    additional_version[0] = '-';
    additional_version[1] = 'm';
    additional_version[2] = 'l';
    additional_version[3] = '-';
    additional_version[4] = build_version[0];
    additional_version[5] = build_version[1];
    additional_version[6] = build_version[2];
    additional_version[7] = build_version[3];
    additional_version[8] = build_version[4];
    additional_version[9] = build_version[5];
    additional_version[10] = build_version[6];
    additional_version[11] = build_version[7];
    additional_version[12] = build_version[8];
    additional_version[13] = '\0';
#endif

    // wait for firmware to initialize
    while (!bmp_vram_raw())
        msleep(100);
    
    // wait for overriden gui_main_task (but use a timeout so it doesn't break if you disable that for debugging)
    for (int i = 0; i < 50; i++)
    {
        if (ml_gui_initialized) break;
        msleep(50);
    }
    msleep(50);

    task_create("ml_init", 0x1e, 0x4000, my_big_init_task, 0 );

    return;
}
