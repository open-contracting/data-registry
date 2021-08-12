var config = {
    apiBaseUrl: "/",
    exporterApiBaseUrl: "/api/"
};

if (process.env.NODE_ENV == "production") {
    Object.assign(config, {
        apiBaseUrl: "/",
        exporterApiBaseUrl: "/api/"
    });
}

export const CONFIG = config;
