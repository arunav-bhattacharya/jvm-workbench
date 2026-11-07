package workbench.container.l01.demo.app;

/** In the package, but not a component: the scanner loads it and skips it. */
public final class MoneyFormat {
    private MoneyFormat() {}

    public static String eur(long minor) { return String.format("EUR %d.%02d", minor / 100, minor % 100); }
}
