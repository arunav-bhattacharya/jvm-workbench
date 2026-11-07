package workbench.container.l01.app;

import workbench.container.l01.Component;

@Component
public class IssuerConfig {
    public String baseUrl() {
        return "https://issuer.example/v2";
    }
}
