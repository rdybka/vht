
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

#endif //__PMS_H__
