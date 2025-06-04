#include <stdio.h>
#include <unistd.h>

int main(void) {
    unsigned long long i = 0;
    while (1) {
        fprintf("%llu\n", i++);
        fflush(stdout);
        usleep(1000000);   // 每 1 秒打印一次，方便观察
    }
}
