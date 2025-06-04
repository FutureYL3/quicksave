#include <stdio.h>
#include <unistd.h>

int main() {
    unsigned long sum = 0;
    for (int i = 0; i < 20; ++ i) {
        printf("add to sum for %d times\n", i + 1);
        sleep(1); // sleep for 1 second
        ++sum;
    }
    printf("sum = %ld\n", sum);
}