package workbench.container.l01.demo.app;

import workbench.container.l01.Component;

@Component
public class SalesBook {
    public SalesBook() {}

    public void add(String line) { System.out.println("  sales book: " + line); }
}
