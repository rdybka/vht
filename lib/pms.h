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

#ifndef __PMS_H__
#define __PMS_H__

#ifdef SWIG
%module pms
    % {
#include "pms.h"
%
}
#endif

extern int start();
extern void stop();

extern int get_bpm();
extern void set_bpm(int);

extern int get_nseq();

extern int add_sequence(int);

extern int get_passthrough();
extern void set_passthrough(int val);

#endif //__PMS_H__
