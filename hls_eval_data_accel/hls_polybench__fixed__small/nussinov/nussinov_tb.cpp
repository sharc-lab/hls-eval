#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "nussinov.h"
#include "hls_eval_check.h"


void init_array (int n,
                 char seq[ 180 + 0],
		 int table[ 180 + 0][180 + 0])
{
  int i, j;


  for (i=0; i <n; i++) {
     seq[i] = (char)((i+1)%4);
  }

  for (i=0; i <n; i++)
     for (j=0; j <n; j++)
       table[i][j] = 0;
}


void print_array(int n,
		 int table[ 180 + 0][180 + 0])

{
  int i, j;
  int t = 0;

  fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
  fprintf(stderr, "begin dump: %s", "table");
  for (i = 0; i < n; i++) {
    for (j = i; j < n; j++) {
      if (t % 20 == 0) fprintf (stderr, "\n");
      fprintf (stderr, "%d ", table[i][j]);
      t++;
    }
  }
  fprintf(stderr, "\nend   dump: %s\n", "table");
  fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}


static bool check_output(int n, int table[ 180 + 0][180 + 0],
			  const std::map<std::string, std::vector<float>> &golden)
{
  int i, j;
  auto it = golden.find("table");
  hls_eval_check::ArrayChecker checker(
      it != golden.end() ? &it->second : nullptr, "table");
  for (i = 0; i < n; i++)
    for (j = i; j < n; j++)
      checker.add((float)table[i][j]);
  return checker.passed();
}


int main(int argc, char** argv)
{

  int n = 180;


   char seq[ 180 + 0];
   int table[ 180 + 0][180 + 0];


  init_array (n, seq, table);


  kernel_nussinov (seq, table);


  print_array(n, table);

  auto golden = hls_eval_check::load_golden_dumps("tb_data.txt");
  bool ok = check_output(n, table, golden);

  return ok ? 0 : 1;
}