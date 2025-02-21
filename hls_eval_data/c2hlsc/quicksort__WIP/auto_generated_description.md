Description:
The QuickSort algorithm is a divide-and-conquer algorithm that sorts an array of integers in ascending order. The algorithm works by selecting a pivot element from the array and partitioning the other elements into two sub-arrays, according to whether they are less than or greater than the pivot. The sub-arrays are then recursively sorted. The partitioning step is implemented using the partition function, which rearranges the array such that all elements less than the pivot are on the left of the pivot, and all elements greater than the pivot are on the right. The quickSort function is the top-level function that orchestrates the sorting process.

Top-Level Function: `quickSort`
Complete Function Signature: `void quickSort(int* arr, int low, int high);`

Inputs:
- `arr`: an array of integers to be sorted, represented as a pointer to an integer array
- `low`: the starting index of the sub-array to be sorted
- `high`: the ending index of the sub-array to be sorted

Outputs:
- none

Important Data Structures and Data Types:
- `int`: a 32-bit signed integer, used to represent the elements of the array
- `int*`: a pointer to an integer, used to represent the array itself

Sub-Components:
- `partition`: a function that partitions the array around a pivot element, rearranging the elements such that all elements less than the pivot are on the left of the pivot, and all elements greater than the pivot are on the right
- `swap`: a function that swaps two elements in the array, used by the partition function to rearrange the elements