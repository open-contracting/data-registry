var config = {
    apiBaseUrl: "/"
};

if (process.env.NODE_ENV == "production") {
    Object.assign(config, {
        apiBaseUrl: "/"
    });
}

export const CONFIG = config;
