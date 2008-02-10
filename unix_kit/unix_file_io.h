/*
 *  unix_file_io.h
 *
 *  These two functions allow unix-style programs
 *  to read and save Triangulations.
 */

#include "SnapPea.h"

extern Triangulation    *read_triangulation(char *file_name);
extern void             write_triangulation(Triangulation *manifold, char *file_name);
