package workbench.startup.l02.fixtures;

/** Its static initializer touches ZoneRules, so initializing ZoneTable loads ZoneRules too. */
public final class ZoneTable {
    static final int[] GRAMS_PER_ZONE = ZoneRules.load();

    private ZoneTable() {
    }

    public static int zoneFor(long grams) {
        return grams <= GRAMS_PER_ZONE[0] ? 1 : 2;
    }
}
