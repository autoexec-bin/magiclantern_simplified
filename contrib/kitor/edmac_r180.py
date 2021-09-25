#!/usr/bin/env python3

"""
* kitor, 25sep2021

Decode DmacInfo and related structures as per R.180 ROM
See https://www.magiclantern.fm/forum/index.php?action=post;topic=26249.0
"""

import sys, argparse
from pprint import pprint

THUMB_FLAG = 0x1
BOOMER_UNDEFINED = 0xFFFFFFFF
BOOMER_InSelTypeMask = 0x0000FF00
BOOMER_AssertInfoMask = 0xFFFF0000

ISRs = {
    0xe05378d6 | THUMB_FLAG : "EDMAC_ReadISR",
    0xe0537990 | THUMB_FLAG : "EDMAC_WriteISR",
    0xe0535c4b | THUMB_FLAG : "EDMAC_UnknownISR",
}

# for DIGIC 8
# https://wiki.magiclantern.fm/digic8
IVT = {
    0x000: "-noise-", 
    0x001: "EDOMAIN_OPERA_OPEKICK0", 
    0x002: "EDOMAIN_EDMAC_5_WR_S1", 
    0x003: "EDOMAIN_EDMAC_1_RD_L0", 
    0x004: "EDOMAIN_VITON", 
    0x005: "EDOMAIN_OPERA0", 
    0x006: "SYNC_irq_intb60v", 
    0x007: "SYNC_vi_out7", 
    0x008: "TMU_int_SWA", 
    0x009: "TMU_int_pulc", 
    0x00A: "INTC_XINT *IRQEXT", 
    0x00B: "TCU_T0OUT *IRQEXT", 
    0x00C: "postman_RCVINT0", 
    0x00D: "postman_FIFOINT0", 
    0x00E: "Eeko_TIMER_OC0_INT*ASYMMETRIC", 
    0x00F: "Eeko_TIMER_IC0_INT*ASYMMETRIC", 
    0x010: "EDOMAIN_SYNGEN_1", 
    0x011: "EDOMAIN_OPERA_OPEKICK1", 
    0x012: "EDOMAIN_EDMAC_6_WR_S0", 
    0x013: "EDOMAIN_EDMAC_1_RD_M0", 
    0x014: "EDOMAIN_AFFINE", 
    0x015: "EDOMAIN_OPERA_ERR0", 
    0x016: "SYNC_irq_intb59v", 
    0x017: "SYNC_vi_out8", 
    0x018: "TMU_int_SWB", 
    0x019: "TMU_int_occh0SP", 
    0x01A: "INTC_XINT *IRQEXT", 
    0x01B: "TCU_T1OUT *IRQEXT", 
    0x01C: "postman_RCVINT1", 
    0x01D: "postman_FIFOINT1", 
    0x01E: "Eeko_TIMER_OC1_INT*ASYMMETRIC", 
    0x01F: "Eeko_TIMER_IC1_INT*ASYMMETRIC", 
    0x020: "EDOMAIN_SYNGEN_2", 
    0x021: "EDOMAIN_OPERA_OPEKICK2", 
    0x022: "EDOMAIN_EDMAC_6_WR_SS0", 
    0x023: "EDOMAIN_EDMAC_1_RD_S0", 
    0x024: "EDOMAIN_AFFINE_OVR_ERR", 
    0x025: "EDOMAIN_OPERA_ABORT0", 
    0x026: "SYNC_irq_intb50v", 
    0x027: "SYNC_vi_out9", 
    0x028: "TMU_int_ocall", 
    0x029: "TMU_int_occh0EP", 
    0x02A: "INTC_XINT *IRQEXT", 
    0x02B: "TCU_T2OUT *IRQEXT", 
    0x02C: "postman_RCVINT2", 
    0x02D: "postman_FIFOINT2", 
    0x02E: "Eeko_TIMER_OC2_INT*ASYMMETRIC", 
    0x02F: "Eeko_TIMER_IC2_INT*ASYMMETRIC", 
    0x030: "EDOMAIN_SYNGEN_3", 
    0x031: "EDOMAIN_OPERA_OPEKICK3", 
    0x032: "EDOMAIN_EDMAC_6_WR_SS1", 
    0x033: "EDOMAIN_EDMAC_1_RD_S1", 
    0x034: "EDOMAIN_SARIDON", 
    0x035: "EDOMAIN_OPERA1", 
    0x036: "SYNC_irq_intb49v", 
    0x037: "SYNC_vi_out10", 
    0x038: "TMU_int_pulgenCEI", 
    0x039: "TMU_int_occh1SP", 
    0x03A: "INTC_XINT *IRQEXT", 
    0x03B: "TCU_T3OUT *IRQEXT", 
    0x03C: "postman_RCVINT3", 
    0x03D: "postman_FIFOINT3", 
    0x03E: "Eeko_TIMER_OC3_INT*ASYMMETRIC", 
    0x03F: "Eeko_TIMER_IC3_INT*ASYMMETRIC", 
    0x040: "EDOMAIN_SYNGEN_4", 
    0x041: "EDOMAIN_OPERA_OPEKICK4", 
    0x042: "EDOMAIN_EDMAC_6_WR_SS2", 
    0x043: "EDOMAIN_EDMAC_1_RD_SS0", 
    0x044: "EDOMAIN_KURABO", 
    0x045: "EDOMAIN_OPERA_ERR1", 
    0x046: "SYNC_irq_intl60v", 
    0x047: "SYNC_vi_out11", 
    0x048: "TMU_int_icapCE1", 
    0x049: "TMU_int_occh1EP", 
    0x04A: "INTC_XINT *IRQEXT", 
    0x04B: "TCU_T4OUT *IRQEXT", 
    0x04C: "postman_RCVINT4", 
    0x04D: "postman_FIFOINT4", 
    0x04E: "Eeko_TIMER_OC4_INT*ASYMMETRIC", 
    0x04F: "Eeko_TIMER_IC4_INT*ASYMMETRIC", 
    0x050: "EDOMAIN_SYNGEN_STP", 
    0x051: "EDOMAIN_OPERA_OPEKICK5", 
    0x052: "EDOMAIN_EDMAC_6_WR_SS3", 
    0x053: "EDOMAIN_EDMAC_1_RD_SS1", 
    0x054: "EDOMAIN_MESSI", 
    0x055: "EDOMAIN_OPERA_ABORT1", 
    0x056: "SYNC_irq_intl60v_st1", 
    0x057: "SYNC_irq_intvi4", 
    0x058: "TMU_pulc_ch0", 
    0x059: "TMU_int_occh2SP", 
    0x05A: "INTC_XINT *IRQEXT", 
    0x05B: "TCU_T5OUT *IRQEXT", 
    0x05C: "postman_RCVINT5", 
    0x05D: "postman_FIFOINT5", 
    0x05E: "Eeko_TIMER_OC5_INT*ASYMMETRIC", 
    0x05F: "Eeko_TIMER_IC5_INT*ASYMMETRIC", 
    0x060: "EDOMAIN_SYNGEN_FRM", 
    0x061: "EDOMAIN_OPERA_OPEKICK6", 
    0x062: "EDOMAIN_EDMAC_6_WR_SS4", 
    0x063: "EDOMAIN_EDMAC_1_RD_SS2", 
    0x064: "EDOMAIN_DANCING_FEN", 
    0x065: "EDOMAIN_HAIDI_PNL_WR", 
    0x066: "SYNC_irq_intl59v", 
    0x067: "SYNC_irq_vi4_set_1", 
    0x068: "TMU_pulc_ch1", 
    0x069: "TMU_int_occh2EP", 
    0x06A: "INTC_XINT *IRQEXT", 
    0x06B: "TCU_IPCOUT4", 
    0x06C: "postman_RCVINT6", 
    0x06D: "postman_FIFOINT6", 
    0x06E: "Eeko_TIMER_OC6_INT*ASYMMETRIC", 
    0x06F: "Eeko_TIMER_IC6_INT*ASYMMETRIC", 
    0x070: "EDOMAIN_SYNGEN_1_A", 
    0x071: "EDOMAIN_EDMAC_1_WR_L0", 
    0x072: "EDOMAIN_EDMAC_DAN_WR", 
    0x073: "EDOMAIN_EDMAC_1_RD_SS3", 
    0x074: "EDOMAIN_DANCING_SURF", 
    0x075: "EDOMAIN_HAIDI_LINE_WR", 
    0x076: "SYNC_irq_intl59v_st1", 
    0x077: "SYNC_irq_vi4_set_2", 
    0x078: "TMU_pulc_ch2", 
    0x079: "TMU_int_occh3SP", 
    0x07A: "INTC_XINT *IRQEXT", 
    0x07B: "TCU_T4F_INT", 
    0x07C: "postman_RCVINT7", 
    0x07D: "postman_FIFOINT7", 
    0x07E: "Eeko_TIMER_OC7_INT*ASYMMETRIC", 
    0x07F: "Eeko_TIMER_IC7_INT*ASYMMETRIC", 
    0x080: "EDOMAIN_SYNGEN_2_A", 
    0x081: "EDOMAIN_EDMAC_1_WR_M0", 
    0x082: "EDOMAIN_EDMAC_7_WR_S0", 
    0x083: "EDOMAIN_EDMAC_2_RD_M0", 
    0x084: "EDOMAIN_DANCING_RACI", 
    0x085: "EDOMAIN_SHREK", 
    0x086: "SYNC_irq_intl50v", 
    0x087: "SYNC_irq_vi4_set_3", 
    0x088: "TMU_pulc_ch3", 
    0x089: "TMU_int_occh3EP", 
    0x08A: "INTC_XINT *IRQEXT", 
    0x08B: "TCU_IPCOUT5", 
    0x08C: "postman_DIRECTINT0", 
    0x08D: "postman_Semaphore0", 
    0x08E: "Eeko_TIMER_ICOC_OC0INT*ASYMMETRIC", 
    0x08F: "Eeko_TIMER_ICOC_IC0INT*ASYMMETRIC", 
    0x090: "EDOMAIN_SYNGEN_3_A", 
    0x091: "EDOMAIN_EDMAC_1_WR_M1", 
    0x092: "EDOMAIN_EDMAC_7_WR_S1", 
    0x093: "EDOMAIN_EDMAC_2_RD_S0", 
    0x094: "EDOMAIN_WOMBAT_INTEG", 
    0x095: "EDOMAIN_SUSAN", 
    0x096: "SYNC_irq_intl50v_st1", 
    0x097: "SYNC_irq_intvi4b", 
    0x098: "Camif", 
    0x099: "TMU_int_occh4SP", 
    0x09A: "INTC_XINT *IRQEXT", 
    0x09B: "TCU_T5F_INT", 
    0x09C: "postman_DIRECTINT1", 
    0x09D: "postman_Semaphore1", 
    0x09E: "Eeko_TIMER_ICOC_OC1INT*ASYMMETRIC", 
    0x09F: "Eeko_TIMER_ICOC_IC1INT*ASYMMETRIC", 
    0x0A0: "EDOMAIN_SYNGEN_4_A", 
    0x0A1: "EDOMAIN_EDMAC_1_WR_M2", 
    0x0A2: "EDOMAIN_EDMAC_7_WR_SS0", 
    0x0A3: "EDOMAIN_EDMAC_2_RD_SS0", 
    0x0A4: "EDOMAIN_WOMBAT_BLOCK", 
    0x0A5: "EDOMAIN_OHYITG", 
    0x0A6: "SYNC_irq_intlssdv", 
    0x0A7: "SYNC_irq_vi4b_set_1", 
    0x0A8: "Camif", 
    0x0A9: "TMU_int_occh4EP", 
    0x0AA: "INTC_XINT *IRQEXT", 
    0x0AB: "Aproc_irq_aproc", 
    0x0AC: "postman_DIRECTINT2", 
    0x0AD: "postman_Semaphore2", 
    0x0AE: "rem_REM_INT", 
    0x0AF: "zico_timer_irq", 
    0x0B0: "EDOMAIN_SYNGEN_STP_A", 
    0x0B1: "EDOMAIN_EDMAC_1_WR_M3", 
    0x0B2: "EDOMAIN_EDMAC_ATO_WR_SS0", 
    0x0B3: "EDOMAIN_EDMAC_3_RD_M0", 
    0x0B4: "EDOMAIN_WOMBAT_AE", 
    0x0B5: "EDOMAIN_HIP", 
    0x0B6: "SYNC_irq_intlssdv_st1", 
    0x0B7: "SYNC_irq_vi4b_set_2", 
    0x0B8: "Camif", 
    0x0B9: "TMU_int_occh5SP", 
    0x0BA: "INTC_XINT *IRQEXT", 
    0x0BB: "Aproc_irq_aproc", 
    0x0BC: "postman_DIRECTINT3", 
    0x0BD: "postman_Semaphore3", 
    0x0BE: "SDDomain_ADMAC0", 
    0x0BF: "HDMAC0_IntrReq1", 
    0x0C0: "EDOMAIN_SYNGEN_FRM_A", 
    0x0C1: "EDOMAIN_EDMAC_1_WR_M4", 
    0x0C2: "EDOMAIN_EDMAC_ATO_WR_SS1", 
    0x0C3: "EDOMAIN_EDMAC_3_RD_OPT_RICH", 
    0x0C4: "EDOMAIN_COMBAT_INTEG", 
    0x0C5: "EDOMAIN_RASH", 
    0x0C6: "SYNC_irq_intp", 
    0x0C7: "SYNC_irq_vi4b_set_3", 
    0x0C8: "Camif", 
    0x0C9: "TMU_int_occh5EP", 
    0x0CA: "INTC_XINT *IRQEXT", 
    0x0CB: "Aproc_irq_aproc", 
    0x0CC: "postman_DIRECTINT4", 
    0x0CD: "postman_fifi_err0", 
    0x0CE: "SDDomain_ADMAC1", 
    0x0CF: "HDMAC0_IntrReq2", 
    0x0D0: "EDOMAIN_SYNGEN_1_B", 
    0x0D1: "EDOMAIN_EDMAC_1_WR_S0", 
    0x0D2: "EDOMAIN_EDMAC_ATO_WR_SS2", 
    0x0D3: "EDOMAIN_EDMAC_3_RD_OPT_LITE", 
    0x0D4: "EDOMAIN_COMBAT_BLOCK", 
    0x0D5: "EDOMAIN_RSHD", 
    0x0D6: "SYNC_irq_intp_st1", 
    0x0D7: "SYNC_vi_out12", 
    0x0D8: "Camif", 
    0x0D9: "TMU_int_icapch0", 
    0x0DA: "INTC_XINT *IRQEXT", 
    0x0DB: "Aproc_irq_aproc", 
    0x0DC: "postman_DIRECTINT5", 
    0x0DD: "SATA_irq_sata", 
    0x0DE: "SDDomain_ADMAC2", 
    0x0DF: "HDMAC0_IntrReq3", 
    0x0E0: "EDOMAIN_SYNGEN_2_B", 
    0x0E1: "EDOMAIN_EDMAC_1_WR_SS0", 
    0x0E2: "EDOMAIN_ORCA_1", 
    0x0E3: "EDOMAIN_EDMAC_DAF_RD_M0", 
    0x0E4: "EDOMAIN_WEABER1", 
    0x0E5: "(reserved)", 
    0x0E6: "SYNC_irq_inte", 
    0x0E7: "Camif", 
    0x0E8: "Camif", 
    0x0E9: "TMU_int_icapch1", 
    0x0EA: "INTC_XINT *IRQEXT", 
    0x0EB: "Aproc_irq_aproc", 
    0x0EC: "postman_DIRECTINT6", 
    0x0ED: "PCIe_irq_pcie", 
    0x0EE: "SDDomain_SDCON0", 
    0x0EF: "HDMAC0_IntrReq4", 
    0x0F0: "EDOMAIN_SYNGEN_3_B", 
    0x0F1: "EDOMAIN_EDMAC_1_WR_SS1", 
    0x0F2: "EDOMAIN_ORCA_2", 
    0x0F3: "EDOMAIN_EDMAC_DAF_RD_S0", 
    0x0F4: "EDOMAIN_WEABER2", 
    0x0F5: "(reserved)", 
    0x0F6: "SYNC_irq_inte_st1", 
    0x0F7: "Camif", 
    0x0F8: "Camif", 
    0x0F9: "TMU_int_icapch2", 
    0x0FA: "INTC_XINT *IRQEXT", 
    0x0FB: "Aproc_irq_aproc", 
    0x0FC: "postman_DIRECTINT7", 
    0x0FD: "PCIe_irq_pcie", 
    0x0FE: "SDDomain_SDCON1", 
    0x0FF: "HDMAC0_IntrReq5", 
    0x100: "EDOMAIN_SYNGEN_4_B", 
    0x101: "EDOMAIN_EDMAC_1_WR_SS2", 
    0x102: "EDOMAIN_ORCA_3", 
    0x103: "EDOMAIN_EDMAC_DAF_RD_S1", 
    0x104: "EDOMAIN_HISTORY", 
    0x105: "(reserved)", 
    0x106: "SYNC_-", 
    0x107: "SSIO_SSIOINT", 
    0x108: "Camif", 
    0x109: "TMU_int_icapch3", 
    0x10A: "INTC_XINT *IRQEXT", 
    0x10B: "Aproc_irq_aproc", 
    0x10C: "cclime_msgcom_int0", 
    0x10D: "PCIe_irq_pcie", 
    0x10E: "SDDomain_SDCON2", 
    0x10F: "HDMAC0_IntrReq6", 
    0x110: "EDOMAIN_SYNGEN_STP_B", 
    0x111: "EDOMAIN_EDMAC_1_WR_SS3", 
    0x112: "EDOMAIN_ORCA_4", 
    0x113: "EDOMAIN_EDMAC_MAP_RD_S0", 
    0x114: "EDOMAIN_HISTORY2_1", 
    0x115: "(reserved)", 
    0x116: "SYNC_-", 
    0x117: "SIO0_SIO0INT", 
    0x118: "Camif", 
    0x119: "TMU_int_icapch4", 
    0x11A: "INTC_XINT *IRQEXT", 
    0x11B: "Aproc_irq_aproc", 
    0x11C: "cclime_msgcom_int1", 
    0x11D: "UHS2_irq_uhs2", 
    0x11E: "XDMAC_XDMAC_0", 
    0x11F: "HDMAC0_IntrReq7", 
    0x120: "EDOMAIN_SYNGEN_FRM_B", 
    0x121: "EDOMAIN_EDMAC_1_WR_SS4", 
    0x122: "EDOMAIN_ORCA_5", 
    0x123: "EDOMAIN_EDMAC_5_RD_M0", 
    0x124: "EDOMAIN_HISTORY2_2", 
    0x125: "(reserved)", 
    0x126: "SYNC_-", 
    0x127: "SIO1_SIO1INT", 
    0x128: "Camif", 
    0x129: "TMU_int_icapch5", 
    0x12A: "INTC_XINT *IRQEXT", 
    0x12B: "Aproc_irq_aproc", 
    0x12C: "cclime_msgcom_int2", 
    0x12D: "UHS2_irq_uhs2", 
    0x12E: "XDMAC_XDMAC_1", 
    0x12F: "irq_mdomain_i2i_0", 
    0x130: "EDOMAIN_HEAD_ERR/ATOMIC_ERR", 
    0x131: "EDOMAIN_EDMAC_1_WR_SS5", 
    0x132: "EDOMAIN_ORCA_6", 
    0x133: "EDOMAIN_EDMAC_5_RD_M1", 
    0x134: "EDOMAIN_HISTORY2_3", 
    0x135: "(reserved)", 
    0x136: "SYNC_-", 
    0x137: "SIO2_SIO2INT", 
    0x138: "Camif", 
    0x139: "TMU_int_icapch6", 
    0x13A: "INTC_XINT *IRQEXT", 
    0x13B: "Aproc_irq_aproc", 
    0x13C: "cclime_msgcom_int3", 
    0x13D: "USB_hibiki_h", 
    0x13E: "XDMAC_XDMAC_2", 
    0x13F: "irq_mdomain_i2i_1", 
    0x140: "EDOMAIN_HEAD_ERR2", 
    0x141: "EDOMAIN_EDMAC_2_WR_M0", 
    0x142: "EDOMAIN_ORCA_7", 
    0x143: "EDOMAIN_EDMAC_5_RD_S0", 
    0x144: "EDOMAIN_HISTORY2_4", 
    0x145: "(reserved)", 
    0x146: "SYNC_irq_lss", 
    0x147: "SIO3_SIO3INT", 
    0x148: "Camif", 
    0x149: "TMU_int_icapch7", 
    0x14A: "INTC_XINT *IRQEXT", 
    0x14B: "adomain_xmon0", 
    0x14C: "cclime_msgcom_int4", 
    0x14D: "USB_hibiki_d", 
    0x14E: "XDMAC_XDMAC_3", 
    0x14F: "irq_mdomain_i2i_2", 
    0x150: "EDOMAIN_HEAD_ERR3", 
    0x151: "EDOMAIN_EDMAC_2_WR_S0", 
    0x152: "EDOMAIN_ORCA_8", 
    0x153: "EDOMAIN_EDMAC_5_RD_SS0", 
    0x154: "EDOMAIN_BIKING", 
    0x155: "TSENS_irq_tsens", 
    0x156: "SYNC_irq_lss_st1", 
    0x157: "SIO4_SIO4INT", 
    0x158: "Camif", 
    0x159: "TMU_int_icapch8", 
    0x15A: "INTC_XINT *IRQEXT", 
    0x15B: "adomain_xmon1", 
    0x15C: "cclime_msgcom_int5", 
    0x15D: "UART0 RX_IntReqRx", 
    0x15E: "DSI_irq_dsi", 
    0x15F: "irq_mdomain_a2i_cclime", 
    0x160: "EDOMAIN_HEAD_ERR4", 
    0x161: "EDOMAIN_EDMAC_2_WR_SS0", 
    0x162: "EDOMAIN_ORCA_9", 
    0x163: "EDOMAIN_EDMAC_5_RD_SS1", 
    0x164: "EDOMAIN_CAPTAIN", 
    0x165: "XDMAC_XDMAC_ABORT", 
    0x166: "SYNC_vi_out0", 
    0x167: "SIO5_SIO5INT", 
    0x168: "Camif", 
    0x169: "TMU_int_icapch9", 
    0x16A: "INCT_XINT *IRQEXT", 
    0x16B: "adomain_xmon2", 
    0x16C: "cclime_msgcom_int6", 
    0x16D: "UART0 TX_IntReqTx", 
    0x16E: "HDMI_irq_hdmi", 
    0x16F: "SROMC0_oIRQ_TX", 
    0x170: "EDOMAIN_HEAD_ERR5", 
    0x171: "EDOMAIN_EDMAC_3_WR_M0", 
    0x172: "EDOMAIN_SWAN_GV_END", 
    0x173: "EDOMAIN_EDMAC_5_RD_SS2", 
    0x174: "EDOMAIN_OPTI0", 
    0x175: "SYNC_vi_out13", 
    0x176: "SYNC_vi_out1", 
    0x177: "SIO6_SIO6INT", 
    0x178: "mario_mario", 
    0x179: "TMU_int_icapch10", 
    0x17A: "INTC_XINT *IRQEXT", 
    0x17B: "adomain_xmon3", 
    0x17C: "cclime_msgcom_int7", 
    0x17D: "UART1 RX_IntReqRx", 
    0x17E: "HDMI_irq_hdmi", 
    0x17F: "SROMC0_oIRQ_RX", 
    0x180: "EDOMAIN_HEAD_ERR6", 
    0x181: "EDOMAIN_EDMAC_3_WR_S0", 
    0x182: "EDOMAIN_PLANET_WR_0", 
    0x183: "EDOMAIN_EDMAC_6_RD_S0", 
    0x184: "EDOMAIN_OPTI1", 
    0x185: "SYNC_vi_out14", 
    0x186: "SYNC_vi_out2", 
    0x187: "SIO7_SIO7INT", 
    0x188: "mario_mario", 
    0x189: "TMU_int_icapch11", 
    0x18A: "INTC_XINT *IRQEXT", 
    0x18B: "cclime_citron_int", 
    0x18C: "cclime_sdcon_int", 
    0x18D: "UART1 TX_IntReqTx", 
    0x18E: "PMU_irq_pmu", 
    0x18F: "SROMC0_oIRQ_FAULT", 
    0x190: "EDOMAIN_SAP1", 
    0x191: "EDOMAIN_EDMAC_3_WR_SS0", 
    0x192: "EDOMAIN_PLANET_WR_1", 
    0x193: "EDOMAIN_EDMAC_6_RD_S1", 
    0x194: "EDOMAIN_DAFIGARO", 
    0x195: "SYNC_vi_out15", 
    0x196: "SYNC_vi_out3", 
    0x197: "swimmy_irq_sitter", 
    0x198: "mario_mario", 
    0x199: "TMU_INT_SWA_ONLY", 
    0x19A: "INTC_XINT *IRQEXT", 
    0x19B: "cclime_tdmac0_int", 
    0x19C: "cclime_others_int", 
    0x19D: "UART2 RX_IntReqRx", 
    0x19E: "HARB_harbInt", 
    0x19F: "SROMC0_oERR_COLLECT", 
    0x1A0: "EDOMAIN_SAP2", 
    0x1A1: "EDOMAIN_EDMAC_DAF_WR_S0", 
    0x1A2: "EDOMAIN_PLANET_RD_0", 
    0x1A3: "EDOMAIN_EDMAC_6_RD_SS0", 
    0x1A4: "EDOMAIN_EDMAC_6_RD_SS5", 
    0x1A5: "SYNC_irq_intvi5", 
    0x1A6: "SYNC_vi_out4", 
    0x1A7: "swimmy_irq_endev", 
    0x1A8: "mario_mario", 
    0x1A9: "TMU_INT_SWB_ONLY", 
    0x1AA: "INCT_XINT *IRQEXT", 
    0x1AB: "cclime_tdmac1_int", 
    0x1AC: "cclime_slotb_sddat1_int *IRQEXT", 
    0x1AD: "UART2 TX_IntReqTx", 
    0x1AE: "RSTGEN_WDTINT", 
    0x1AF: "SROMC1_oIRQ_TX", 
    0x1B0: "EDOMAIN_SAP3", 
    0x1B1: "EDOMAIN_EDMAC_MAP_WR_SS0", 
    0x1B2: "EDOMAIN_PLANET_RD_1", 
    0x1B3: "EDOMAIN_EDMAC_6_RD_SS1", 
    0x1B4: "EDOMAIN_EDMAC_6_RD_SS6", 
    0x1B5: "dolphin", 
    0x1B6: "SYNC_vi_out5", 
    0x1B7: "swimmy_irq_sven", 
    0x1B8: "mario_mario", 
    0x1B9: "TMU_INT_SWC_ONLY", 
    0x1BA: "INTC_XINT *IRQEXT", 
    0x1BB: "cclime_tdmac2_int", 
    0x1BC: "cclime_slotd_sddat1_int *IRQEXT", 
    0x1BD: "I2C0_TIRQ", 
    0x1BE: "I2C1_TIRQ", 
    0x1BF: "SROMC1_oIRQ_RX", 
    0x1C0: "EDOMAIN_ATOMIC_LIP", 
    0x1C1: "EDOMAIN_EDMAC_MAP_WR_SS1", 
    0x1C2: "EDOMAIN_JP52", 
    0x1C3: "EDOMAIN_EDMAC_6_RD_SS2", 
    0x1C4: "EDOMAIN_EDMAC_6_RD_SS7", 
    0x1C5: "dolphin", 
    0x1C6: "SYNC_vi_out6", 
    0x1C7: "ALGS_irq_algs", 
    0x1C8: "mario_mario", 
    0x1C9: "TMU_INT_SWD_ONLY", 
    0x1CA: "INTC_IRQ_soft_out*ASYMMETRIC", 
    0x1CB: "cclime_tdmac3_int", 
    0x1CC: "(reserved)", 
    0x1CD: "I2C0_RIRQ", 
    0x1CE: "I2C1_RIRQ", 
    0x1CF: "SROMC1_oIRQ_FAULT", 
    0x1D0: "EDOMAIN_PENTA", 
    0x1D1: "EDOMAIN_EDMAC_5_WR_M0", 
    0x1D2: "EDOMAIN_EDMAC_OPERA_WR", 
    0x1D3: "EDOMAIN_EDMAC_6_RD_SS3", 
    0x1D4: "EDOMAIN_EDMAC_DAN_RD", 
    0x1D5: "dolphin", 
    0x1D6: "int_tm_misc_cpu_handshake0*ASYMMETRIC", 
    0x1D7: "ALGS_irq_algs", 
    0x1D8: "mario_mario", 
    0x1D9: "irq_mcpu_SCUEVABORT *IRQEXT", 
    0x1DA: "irq_mcpu_SLVERRINTR", 
    0x1DB: "irq_mcpu", 
    0x1DC: "(reserved)", 
    0x1DD: "I2C0_SIRQ", 
    0x1DE: "I2C1_SIRQ", 
    0x1DF: "SROMC1_oERR_COLLECT", 
    0x1E0: "EDOMAIN_SANTA", 
    0x1E1: "EDOMAIN_EDMAC_5_WR_S0", 
    0x1E2: "EDOMAIN_EDMAC_OPERA_RD", 
    0x1E3: "EDOMAIN_EDMAC_6_RD_SS4", 
    0x1E4: "EDOMAIN_EDMAC_7_RD_S0", 
    0x1E5: "dolphin", 
    0x1E6: "int_tm_misc_cpu_handshake1*ASYMMETRIC", 
    0x1E7: "GLDA_irq_glda", 
    0x1E8: "mario_mario", 
    0x1E9: "irq_mcpu_DECERRINTR", 
    0x1EA: "irq_mcpu_L2CCINTR", 
    0x1EB: "irq_mcpu", 
    0x1EC: "MONI_moniout(0)*IRQEXT", 
    0x1ED: "MONI_moniout(1)*IRQEXT", 
    0x1EE: "MONI_moniout(2)*IRQEXT", 
    0x1EF: "MONI_moniout(3)*IRQEXT", 
    0x1F0: "INTC_ANDINT(0)*ASYMMETRIC", 
    0x1F1: "INTC_ANDINT(1)*ASYMMETRIC", 
    0x1F2: "INTC_ANDINT(2)*ASYMMETRIC", 
    0x1F3: "INTC_ANDINT(3)*ASYMMETRIC", 
    0x1F4: "INTC_ANDINT(4)*ASYMMETRIC", 
    0x1F5: "INTC_ANDINT(5)*ASYMMETRIC", 
    0x1F6: "DEBSIO", 
    0x1F7: "XIMR_irq_ximr", 
    0x1F8: "mario_mario", 
    0x1F9: "irq_mcpu_ECNTRINTR", 
    0x1FA: "INTC_ANDINT(0)*ASYMMETRIC", 
    0x1FB: "INTC_ANDINT(1)*ASYMMETRIC", 
    0x1FC: "INTC_ANDINT(2)*ASYMMETRIC", 
    0x1FD: "INTC_ANDINT(3)*ASYMMETRIC", 
    0x1FE: "INTC_ANDINT(4)*ASYMMETRIC", 
    0x1FF: "INTC_ANDINT(5)*ASYMMETRIC",
}

# For easier Ghidra decomp reading:
# 0x0e INFO_VITON_MODE
# 0x0F INFO_OPTI_MODE
# 0x13 INFO_XSYS_DIV_MODE
# 0x14 INFO_DIV_MODE
# 0x15 INFO_32BIT_MODE
# 0x16 INFO_64BIT_MODE
# 0x17 INFO_128BIT_MODE
# 0x18 INFO_DMAC_DANCING
# 0x1D INFO_DMAC_SS
# 0x1E INFO_DMAC_TYPE_READ
# & 1  INFO_DMAC_TYPE_WRITE

# Engine::Edmac.c
flags = {
    0x0  : "INFO_DMAC_TYPE_WRITE",
    0x1  : "INFO_DMAC_TYPE_READ", 
    0x2  : "INFO_DMAC_SS",
    0x7  : "INFO_DMAC_DANCING", 
    0x8  : "INFO_128BIT_MODE", 
    0x9  : "INFO_64BIT_MODE", 
    0xA  : "INFO_32BIT_MODE", 
    0xB  : "INFO_DIV_MODE",
    0xC  : "INFO_XSYS_DIV_MODE", 
    0x10 : "INFO_OPTI_MODE", 
    0x11 : "INFO_VITON_MODE",
}

# Engine::Edmac.c
PackUnpackModeFlags = {
    0x0  : "INFO_PACK_UNPACK_MODE",
    0x1  : "INFO_PACK_UNPACK_XMODE",
}

# Engine::BoomerVdKick.c
BoomerVdType = {
    0x1 : "E_BOOMER_VD_KICK",
}

# Engine::ChaseCtl.c, no relation found so far to EDMAC ID
ChasePort = {
    0x2e : "ELD_EDMAC_CHASER_EMPTY"
}

# Engine::BoomerSreset.c, no relation found so far to EDMAC ID
# This is matched to BoomerID
SelectId = {
    0xD70000: "ELD_BOOMER_DAFIGARO_1",
    0xD80000: "ELD_BOOMER_DAFIGARO_2",
    0xD90000: "ELD_BOOMER_DAFIGARO_3",
}
    
def is_set(x,n):
    return x & n != 0

def gen_range():
    out = []
    for i in range(32):
        out.append(1 << i)
    return out
    
class Globals:
    file = None
    rom_base = 0xE0000000

    flagPowers = []

    TotalChannels      = 76
    TotalPackUnpack    = 0
    BoomerVdKick_total = 265
    BoomerSelector_total = 225

    DmacInfo          = 0xE0DD5C64 - rom_base
    InterruptHandlers = 0xE0DD641C - rom_base
    PackUnpackId      = 0xe0dd5b34 - rom_base
    PackUnpackInfo    = 0xe0dd5ec4 - rom_base
    DmacBoomerInfo    = 0xe0dd608c - rom_base
    BoomerVdKickInfo  = 0xe0f73510 - rom_base
    BoomerSelector1   = 0xe0f72e08 - rom_base
    BoomerInputPort   = 0xe0f7318c - rom_base
    
def getDmacInfo():
    DmacInfo = {}
    with open(Globals.file, "rb") as rom_file:
        rom_file.seek(Globals.DmacInfo, 0)
        print("DmacInfo start: {}".format(hex(rom_file.tell())))
        
        for i in range(Globals.TotalChannels):
            addr = rom_file.read(4)
            flag = rom_file.read(4)
            
            addr = int.from_bytes(addr, byteorder='little')
            flag = int.from_bytes(flag, byteorder='little')
            
            DmacInfo[i] = [addr, flag]
    return DmacInfo
    
def getInterruptHandlers():
    arr = {}
    with open(Globals.file, "rb") as rom_file:
        rom_file.seek(Globals.InterruptHandlers, 0)
        print("InterruptHandlers start: {}".format(hex(rom_file.tell())))
        for i in range(Globals.TotalChannels):        
            unk = rom_file.read(4)
            cbr = rom_file.read(4)
            
            unk = int.from_bytes(unk, byteorder='little')
            cbr = int.from_bytes(cbr, byteorder='little')
            arr[i] = [unk, cbr]
    return arr


def getPackUnpackId():
    arr = []
    with open(Globals.file, "rb") as rom_file:
        rom_file.seek(Globals.PackUnpackId, 0)
        print("PackUnpackId start: {}".format(hex(rom_file.tell())))
        for i in range(Globals.TotalChannels):
            id = rom_file.read(4)
            id = int.from_bytes(id, byteorder='little')
            arr.append(id)
    Globals.TotalPackUnpack = max(arr)
    return arr


def getPackUnpackInfo():
    arr = {}
    with open(Globals.file, "rb") as rom_file:
        rom_file.seek(Globals.PackUnpackInfo, 0)
        print("PackUnpackInfo start: {}".format(hex(rom_file.tell())))
        for i in range(Globals.TotalChannels):
            ptr = rom_file.read(4)
            unk = rom_file.read(4)
            inf = rom_file.read(4)

            ptr = int.from_bytes(ptr, byteorder='little')
            unk = int.from_bytes(unk, byteorder='little')
            inf = int.from_bytes(inf, byteorder='little')
            arr[i] = [ptr, unk, inf]
    return arr;

# BoomerID
# 0xFFFFFFFF: BOOMER_UNDEFINED
#
# InSelType
# flags | 0x0000FF00 InSelType
# flags | 0xFFFF0000 AssertInfo
#

def getDmacBoomerInfo():
    arr = {}
    with open(Globals.file, "rb") as rom_file:
        rom_file.seek(Globals.DmacBoomerInfo, 0)
        print("DmacBoomerInfo start: {}".format(hex(rom_file.tell())))
        for i in range(Globals.TotalChannels):
            id = rom_file.read(4)
            type = rom_file.read(4)
            edmac_type = rom_file.read(4)

            id = int.from_bytes(id, byteorder='little')
            type = int.from_bytes(type, byteorder='little')
            edmac_type = int.from_bytes(edmac_type, byteorder='little')
            arr[i] = [id, type, edmac_type]
    return arr;

def getBoomerVdKickInfo():
    arr = {}
    with open(Globals.file, "rb") as rom_file:
        rom_file.seek(Globals.BoomerVdKickInfo, 0)
        print("BoomerVdKickInfo start: {}".format(hex(rom_file.tell())))
        for i in range(Globals.BoomerVdKick_total):
            VdType = rom_file.read(4)
            addr1 = rom_file.read(4)
            addr2 = rom_file.read(4)

            VdType = int.from_bytes(VdType, byteorder='little')
            addr1 = int.from_bytes(addr1, byteorder='little')
            addr2 = int.from_bytes(addr2, byteorder='little')
            arr[i] = [VdType, addr1, addr2]
    return arr;
    
def getBoomerSelector1():
    arr = []
    with open(Globals.file, "rb") as rom_file:
        rom_file.seek(Globals.BoomerSelector1, 0)
        print("BoomerSelector1 start: {}".format(hex(rom_file.tell())))
        for i in range(Globals.BoomerSelector_total):
            id = rom_file.read(4)
            id = int.from_bytes(id, byteorder='little')
            arr.append(id)
    return arr
    
def getBoomerInputPort():
    arr = []
    with open(Globals.file, "rb") as rom_file:
        rom_file.seek(Globals.BoomerInputPort, 0)
        print("BoomerInputPort start: {}".format(hex(rom_file.tell())))
        for i in range(Globals.BoomerSelector_total):
            id = rom_file.read(4)
            id = int.from_bytes(id, byteorder='little')
            arr.append(id)
    return arr
    
def decodeModeInfo():
    DmacInfo         = getDmacInfo()
    ISRArr           = getInterruptHandlers()
    PackUnpackId     = getPackUnpackId()
    PackUnpackInfo   = getPackUnpackInfo()
    DmacBoomerInfo   = getDmacBoomerInfo()
    BoomerVdKickInfo = getBoomerVdKickInfo()
    BoomerSelector1  = getBoomerSelector1()
    BoomerInputPort  = getBoomerInputPort()

    for i in range(Globals.TotalChannels):
        print("================================================================")
        print("ID: {:>2}, addr: {}".format(i, hex(DmacInfo[i][0])))

        print("FLAGS {:#032b}".format( DmacInfo[i][1]))
        print("  INDEX: FLAG_NAME")
        for bit, mask in enumerate(Globals.flagPowers):
            tmp = flags[bit] if bit in flags.keys() else "__INFO_{}".format(hex(bit))
            if is_set(DmacInfo[i][1], mask):
                print("     {:>2}: {}".format(bit, tmp))
        print()

        tmp = ISRs[ISRArr[i][1]] if ISRArr[i][1] in ISRs.keys() else "?"
        print("Interrupt") 
        print("    ID : 0x{:03x}      {}".format(ISRArr[i][0], IVT[ISRArr[i][0]] ))
        print("    ISR: {} {}".format(hex(ISRArr[i][1]), tmp))
        print()
    
        puid = PackUnpackId[i]    
        mode = PackUnpackInfo[puid][2]
        tmp = PackUnpackModeFlags[mode] if mode in PackUnpackModeFlags.keys() else "__UNKNOWN_{}".format(mode)
        if mode:
            print("PackUnpackInfo")
            print("    PackUnpackId      : {}".format(puid))
            print("    ptr               : {}".format(hex(PackUnpackInfo[puid][0])))
            print("    unk               : {}".format(PackUnpackInfo[puid][1]))
            print("PackUnpackInfoMode")
            for bit, mask in enumerate(Globals.flagPowers):
                if is_set(mode, mask):
                    tmp = PackUnpackModeFlags[bit] if bit in PackUnpackModeFlags.keys() else "__INFO_PACK_{}".format(hex(bit))
                    print("    {:>2}: {}".format(bit, tmp))
            print()

        BoomerID = DmacBoomerInfo[i][0];
        print("DmacBoomerInfo {}".format( "BOOMER_UNDEFINED" if BoomerID == BOOMER_UNDEFINED else hex(BoomerID)))
        if BoomerID != BOOMER_UNDEFINED:
            print("    BoomerInSelType         : 0x{:08x}".format(DmacBoomerInfo[i][1]))
            print("        `-- & InSelType     : 0x{:08x}".format(DmacBoomerInfo[i][1] & BOOMER_InSelTypeMask))
            print("    BoomerInSelEdmacType    : 0x{:08x}".format(DmacBoomerInfo[i][2]))
            print("        `-- & AssertInfo    : 0x{:08x}".format(DmacBoomerInfo[i][2] & BOOMER_AssertInfoMask))

            VdKickId = BoomerID >> 0x10
            print("BoomerVdKickInfo for BoomerID {} ({})".format(hex(BoomerID), hex(VdKickId)))
            VdType   = BoomerVdKickInfo[VdKickId][0]
            print("    VdType                  : {} {}".format(
                hex(VdType),
                BoomerVdType[VdType] if VdType in BoomerVdType.keys() else "__UNKNOWN_{}".format(hex(VdType))))
            print("    addr1                   : {}".format(hex(BoomerVdKickInfo[VdKickId][1])))
            print("    addr2                   : {}".format(hex(BoomerVdKickInfo[VdKickId][2])))
            
            if VdType == 0x1: # Two address arrays are defined only for E_BOOMER_VD_KICK
                print("BoomerSelector for {}".format(hex(BoomerID)))
                print("    addr1               : {}".format(hex(BoomerSelector1[VdKickId])))
                print("    addr2 (InputPort?)  : {}".format(hex(BoomerInputPort[VdKickId])))

        print()
    return

parser = argparse.ArgumentParser(description="Decode DM buffers")

file_args = parser.add_argument_group("Input file")
file_args.add_argument("file", default="ROM1.bin", help="ROM dump to analyze")
args = parser.parse_args()

Globals.file = args.file
Globals.flagPowers = gen_range()
decodeModeInfo()
