#include <crow.h>

int main() {
    crow::SimpleApp app;

    CROW_ROUTE(app, "/")
    ([] {
        return crow::response(200, "SentinelX C++ service");
    });

    CROW_ROUTE(app, "/health")
    ([] {
        return crow::response(200, "OK");
    });

    CROW_ROUTE(app, "/api/work")
    ([] {
        volatile long long x = 0;

        for (long long i = 0; i < 100000000; i++)
            x += i;

        return crow::response(200, "work completed");
    });

    app.port(8080).multithreaded().run();

    return 0;
}
