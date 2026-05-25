#!/bin/bash
find . \( -name ".git" -o -name "node_modules" \) -prune -o -type d -mmin -180 -printf "%TI:%TM : %p\n" | sort

