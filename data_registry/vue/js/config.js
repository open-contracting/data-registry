var config = {
    apiBaseUrl: "http://localhost:8000/"
};

if (process.env.NODE_ENV == "production") {
    Object.assign(config, {
        apiBaseUrl: ""
    });
}

export const CONFIG = config;
