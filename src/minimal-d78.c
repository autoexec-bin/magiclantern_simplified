/** \file
 * Minimal test code for DIGIC 7 & 8
 * ROM dumper & other experiments
 */

 #include "dryos.h"
 #include "vram.h"
 #include "bmp.h"

static void led_blink(int times, int delay_on, int delay_off)
{
    for (int i = 0; i < times; i++)
    {
        MEM(CARD_LED_ADDRESS) = LEDON;
        msleep(delay_on);
        MEM(CARD_LED_ADDRESS) = LEDOFF;
        msleep(delay_off);
    }
}

extern int uart_printf(const char *fmt, ...);

extern void *_alloc_dma_memory(size_t size);

#undef malloc
#undef free
#undef _alloc_dma_memory
#define malloc _alloc_dma_memory
#define free _free_dma_memory

/*
 * kitor: So I found a compositor on EOSR
 * Uses up to 6 RGBA input layers, but Canon ever alocates only two.
 *
 * This uses RGBA layers that @coon noticed on RP long time ago.
 *
 * Layers are stored from bottom (0) to top (5). Canon uses 0 for GUI
 * and 1 for overlays in LV mode (focus overlay)
 *
 * I was able to create own layer(s), drawn above two Canon pre-alocated ones.
 * This PoC will alocate one new layer on top of existing two, and use that
 * buffer to draw on screen.
 *
 * Tested (briefly) on LV, menus, during recording, playback, also on HDMI.
 *
 * The only cavieat that I was able to catch was me calling redraw while GUI
 * also wanted to redraw screen. This "glitched" by showing partialy rendered
 * frame. Shouldn't be an issue while we have a control over GUI events.
 *
 * But since we don't have to constantly redraw until we want to update the
 * screen - there's no need to fight with Canon code.
 *
 * For drawing own LV overlays it should be enough to disable layers 0 (GUI)
 * and maybe 1 (AF points, AF confirmation).
 * LV calls redraw very often, so probably we don't need to call it ourselfs
 * in that mode.
 */

/*
 * Family of functions new to compositor.
 * Terminology:
 * XCM  - X Compositing Manager (?). Referred almost everywhere.
 * Ximr - X image renderer (?). See XCMStatus EvShell command output.
 * XOC  - Ximr Output Chunk.
 */
extern uint32_t *XCM_GetOutputChunk(
    uint8_t  **ppXimrContext,
    uint32_t   outChunkID
);
extern uint32_t XCM_SetSourceArea(
    uint8_t  **ppXimrContext,
    uint32_t   layerID,
    uint16_t   x,
    uint16_t   y,
    uint16_t   w,
    uint16_t   h
 );
extern uint32_t XCM_SetSourceSurface(
    uint8_t     **ppXimrContext,
    uint32_t      layerID,
    struct MARV  *pSrcMARV
);
extern uint32_t XOC_SetLayerEnable(
    uint32_t    *pOutChunk,
    uint32_t     layerID,
    struct MARV *pSrcMARV
);

/*
 * XCM_SetRefreshDisplay() will just set memory location. 0xFE6C in R180
 *
 * Stub names for those two should be changed. 200d, while (probably)
 * not having a compositor - has similar (less advanced) RefreshDisplay()
 * function, and memory location being equivalent of what XCM_SetRefreshDisplay
 * writes into.
 *
 * Thus I propose just RefreshDisplay() and use memory location directly
 * instead of calling XCM_SetRefreshDisplay - for compatibility reasons.
 */
extern void XCM_SetRefreshDisplay(int state);
extern void XCM_RefreshDisplay();

/*
 * All the important memory structures.
 *
 * XCM_RendererLayersArr holds MARV struct pointers to layers created by
 *                       RENDERER_InitializeScreen(). Those are layers created
 *                       by Canon GUI renderer code.
 * XCM_LayersArr         Like above, but used by XCM for rendering setup.
 *                       Entries from array above are copied in (what I called)
 *                       Initialize_Renedrer() after RENDERER_InitializeScreen()
 *                       and VMIX_InitializeScreen() are done.
 * XCM_LayersEnableArr   Controls if layer with given ID is displayed or not.
 *                       Set up just after XCM_LayersArr is populated.
 * XCM_Inititialized     Variable set by XCM_RefreshDisplay after it initialized
 *                       XCM (XCM_Reset(), ... ). Init ends with debug message
 *                       containing "initializeXimrContext".
 * XimrContext           Internal structure used by XCM for Ximr configuration.
 */
extern struct MARV **XCM_RendererLayersArr[];
extern struct MARV **XCM_LayersArr[];
extern uint32_t     *XCM_LayersEnableArr[];
extern uint32_t     *XCM_Inititialized;
extern uint8_t     **XimrContext;

/*
 * Just a pointer to MARV four our own layer, plus layer ID for toggling later.
 */
struct MARV *rgb_vram_info = 0x0; //our layer
int _rgb_vram_layer = 0;

/*
 * Some defines. Should be renamed to fit bmp.h
 */
#define BUF_W          960
#define BUF_H          540
#define BMP_VRAM_SIZE  (BUF_W*BUF_H*4) //*4 as vram.h MARV buffer is uint8_t*
#define BMP_W          720             // not whole buffer is used to display
#define BMP_H          480             // only center part
#define BMP_W_OFF      120
#define BMP_H_OFF       30
#define XCM_MAX_LAYERS   6             //This is hardcoded on R/RP code

/*
 * Not sure if sync_caches() call is needed. It was when I was drawing
 * over Canon buffers, but now when we have our own may be unncesessary.
 */
static void surface_redraw()
{
    XCM_SetRefreshDisplay(1);
    sync_caches();
    XCM_RefreshDisplay();
}

/*
 * This array toggles coresponding layers. What is weird, this has no effect
 * on XCMStatus command output, they will still be seen as "enabled":
 *
 * [Input Layer] No:2, Enabled:1
 *  VRMS Addr:0x000e0c08, pImg:0x00ea6d54, pAlp:0x00000000, W:960, H:540
 *  Color:=0x05040100, Range:FULL
 *  srcX:0120, srcY:0030, srcW:0720, srcH:0480, dstX:0000, dstY:0000
 */
static void surface_set_visibility(int state)
{
    if((XCM_Inititialized == 0) || (rgb_vram_info == 0x0))
        return;

    XCM_LayersEnableArr[_rgb_vram_layer] = state;
    //do we want to call redraw, or leave it to the caller?
    surface_redraw();
}

/*
 * Create a new VRAM (MARV) structure, alloc buffer for VRAM.
 * Call compositor to enable newly created layer.
 */
static int surface_setup()
{
    //just in case we raced renderer init code.
    if(XCM_Inititialized == 0)
        return 1;

    //may differ per camera? R and RP have 6.
    int newLayerID = 0;
    for(int i = 0; i < XCM_MAX_LAYERS; i++)
    {
        if(XCM_LayersArr[i] == 0x0)
            break;

        newLayerID++;
    }

    uart_printf("Found %d layers\n", newLayerID);
    if(newLayerID >= XCM_MAX_LAYERS)
    {
        uart_printf("Too many layers: %d/%d, aborting!\n",
                newLayerID, XCM_MAX_LAYERS);
        return 1;
    }

    /*
     * In theory XCM can have multiple (4?) XimrContext chunks.
     * But the only code that Canon uses to call this function has 0 hardcoded.
     * Thus, at least on R I don't expect more to exists.
     */
    uart_printf("XimrContext at 0x%08x\n", XimrContext);
    uint32_t *pOutChunk = XCM_GetOutputChunk(XimrContext, 0);
    if(pOutChunk == 0x0)
        return 1;

    uart_printf("pOutChunk   at 0x%08x\n", pOutChunk);

    struct MARV* pNewLayer = malloc(sizeof(struct MARV));
    uint8_t* pBitmapData = malloc(BMP_VRAM_SIZE);
    if((pNewLayer == 0x0) || (pBitmapData == 0x0))
    {
        uart_printf("New layer preparation failed.\n");
        return 1;
    }

    //clean up new surface
    bzero32(pBitmapData, BMP_VRAM_SIZE);

    /*
     * Lazy way to create a new MARV structure. Just copy other one,
     * and update bitmap data and permament memory pointers.
     */
    memcpy(pNewLayer, XCM_LayersArr[newLayerID - 1], sizeof(struct MARV));
    pNewLayer->bitmap_data = pBitmapData;
    //erase PMEM pointer as it is not valid and required anymore.
    pNewLayer->pmem = 0x0;
    
    uart_printf("pNewLayer   at 0x%08x\n", pNewLayer);
    uart_printf("pBitmapData at 0x%08x\n", pBitmapData);

    //add new layer to compositor layers array
    XCM_LayersArr[newLayerID] = pNewLayer;

    //enable new layer - just in case (all were enabled by default on R180)
    XCM_LayersEnableArr[newLayerID] = 0x1;

    //call compositor to add new layer to render
    XCM_SetSourceArea(XimrContext, newLayerID,
            BMP_W_OFF, BMP_H_OFF, BMP_W, BMP_H);
    XCM_SetSourceSurface(XimrContext, newLayerID, pNewLayer);
    XOC_SetLayerEnable(pOutChunk, newLayerID, pNewLayer);

    //save rgb_vram_info as last step, in case something above fails.
    rgb_vram_info   = pNewLayer;
    _rgb_vram_layer = newLayerID;

    return 0;
}

void rgba_fill(uint32_t color, int x, int y, int w, int h)
{
    if(rgb_vram_info == 0x0)
    {
      uart_printf("ERROR: rgb_vram_info not initialized\n");
      return;
    }

    //Note: buffers are GBRA :)
    uint32_t *b = rgb_vram_info->bitmap_data;
    for (int i = y; i < y + h; i++)
    {
        uint32_t *row = b + 960*i + x;
        for(int j = x; j < x + w; j++)
            *row++ = color;
    }

    surface_redraw();
}

static void test_compositor_task(){
    //call method to init surface
    while (surface_setup())
        msleep(500);

    //draw semi-transparent rectangle
    rgba_fill(0xDEADBEEF, 200, 300, 200, 200);
    surface_redraw();

    //toggle visibility in a loop
    while(1)
    {
        surface_set_visibility(1);
        msleep(1000);
        surface_set_visibility(0);
        msleep(1000);
    }
}
/* called before Canon's init_task */
void boot_pre_init_task(void)
{
    /* nothing to do */
}

/* called right after Canon's init_task, while their initialization continues in background */
void boot_post_init_task(void)
{
    msleep(1000);

    task_create("test_compositor", 0x1e, 0x1000, test_compositor_task, 0 );
}

void disp_set_pixel(int x, int y, int c){}
