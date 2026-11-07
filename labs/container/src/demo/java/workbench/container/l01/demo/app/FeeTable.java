package workbench.container.l01.demo.app;

import workbench.container.l01.Component;

@Component
public class FeeTable {
    static {
        System.out.println("  FeeTable.<clinit>: loading 40,000 fee rows");   // runs on first active use only
    }
}
