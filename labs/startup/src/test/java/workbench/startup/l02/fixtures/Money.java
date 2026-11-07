package workbench.startup.l02.fixtures;

final class Money {
    private Money() {
    }

    static String format(long minor) {
        return (minor / 100) + "." + (minor % 100 < 10 ? "0" : "") + (minor % 100) + " EUR";
    }
}
