#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>
#include "xrfdc_clk.h"

int writeLmk04208Regs(int IicNum, unsigned int RegVals[26]) {
    unsigned int LMK04208_CKin[1][26];
    for(int i=0;i<26;i++)
	    LMK04208_CKin[0][i] = RegVals[i];
    LMK04208ClockConfig(IicNum, LMK04208_CKin);

     // We really should be returning exit status here!
     // Need to patch xrfdc_clk.c file to return status.
     return 0;
 }

int writeLmx2594Regs(int IicNum, unsigned int RegVals[113]) {
    int XIicDevFile;
    char XIicDevFilename[20];

    sprintf(XIicDevFilename, "/dev/i2c-%d", IicNum);
    XIicDevFile = open(XIicDevFilename, O_RDWR);

    if (ioctl(XIicDevFile, I2C_SLAVE_FORCE, 0x2f) < 0) {
      printf("Error: Could not set address \n");
      return 1;
    }

    Lmx2594Updatei2c(XIicDevFile, RegVals);

    close(XIicDevFile);

    // Should really get a return code from Lmx2594Updatei2c!
    // Requires patch to xrfdc_clk.c.
    return 0;
}
