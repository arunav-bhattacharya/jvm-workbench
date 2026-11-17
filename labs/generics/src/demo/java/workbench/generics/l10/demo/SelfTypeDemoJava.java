package workbench.generics.l10.demo;

/** Java twin of SelfTypeDemo.kt. The same recursive bound that java.lang.Enum uses: Enum<E extends Enum<E>>. */
public class SelfTypeDemoJava {

    static class PlainBuilder {
        protected int grams;
        PlainBuilder grams(int grams) { this.grams = grams; return this; }
    }
    static final class PlainGiftBoxBuilder extends PlainBuilder {
        private String ribbon = "";
        PlainGiftBoxBuilder ribbon(String colour) { ribbon = colour; return this; }
        String build() { return "gift box, " + grams + " g, " + ribbon + " ribbon"; }
    }

    static abstract class Builder<B extends Builder<B>> {
        protected int grams;
        B grams(int grams) { this.grams = grams; return self(); }
        protected abstract B self();
    }
    static final class GiftBoxBuilder extends Builder<GiftBoxBuilder> {
        private String ribbon = "";
        GiftBoxBuilder ribbon(String colour) { ribbon = colour; return this; }
        @Override protected GiftBoxBuilder self() { return this; }
        String build() { return "gift box, " + grams + " g, " + ribbon + " ribbon"; }
    }

    public static void main(String[] args) {
        PlainBuilder lost = new PlainGiftBoxBuilder().ribbon("red").grams(1_200);   // grams() returns a PlainBuilder
        System.out.println("after grams(): static type PlainBuilder, run-time class " + lost.getClass().getSimpleName());
        System.out.println(new GiftBoxBuilder().grams(1_200).ribbon("red").build());

        // Wrong move. Uncomment, predict the error, then run.
        // System.out.println(new PlainGiftBoxBuilder().grams(1_200).ribbon("red").build());
    }
}
