
#ifndef __PMS_H__
#define __PMS_H__

#ifdef SWIG
%module pms
%{
#include "pms.h"
%}
#endif


extern int start();
extern void stop();

extern int get_passthrough();
extern void set_passthrough(int val);

#endif //__PMS_H__
