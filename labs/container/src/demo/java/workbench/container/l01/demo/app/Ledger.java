package workbench.container.l01.demo.app;

import workbench.container.l01.Component;

@Component
public class Ledger {
    public Ledger() {}

    public void post(String line) { System.out.println("  ledger: " + line); }
}
