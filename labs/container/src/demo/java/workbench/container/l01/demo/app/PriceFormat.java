package workbench.container.l01.demo.app;

/** In the package, but not a component: the scanner loads it and skips it. */
public final class PriceFormat {
    private PriceFormat() {}

    public static String euros(long cents) { return String.format("EUR %d.%02d", cents / 100, cents % 100); }
}
