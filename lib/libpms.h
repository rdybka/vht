/* pms.h
 *
 * Copyright (C) 2017 Remigiusz Dybka
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef __LIBPMS_H__
#define __LIBPMS_H__

#ifdef SWIG
%module libpms
%{
#include "libpms.h"
%}
#endif

#include "module.h"

extern int start();
extern void stop();

// module
extern void module_new();
extern void module_free();
extern void module_play(int);
extern int module_is_playing();
extern void module_reset();

extern int module_get_bpm();
extern void module_set_bpm(int);

extern int module_get_nseq();
sequence *module_get_seq(int);

#endif //__LIBPMS_H__
