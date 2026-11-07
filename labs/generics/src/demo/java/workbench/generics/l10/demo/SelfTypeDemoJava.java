package workbench.generics.l10.demo;

/** Java twin of SelfTypeDemo.kt. The same recursive bound that java.lang.Enum uses: Enum<E extends Enum<E>>. */
public class SelfTypeDemoJava {

    static class PlainBuilder {
        protected long cents;
        PlainBuilder amount(long cents) { this.cents = cents; return this; }
    }
    static final class PlainCardBuilder extends PlainBuilder {
        private String token = "";
        PlainCardBuilder cardToken(String t) { token = t; return this; }
        String build() { return "card " + cents + " with " + token; }
    }

    static abstract class Builder<B extends Builder<B>> {
        protected long cents;
        B amount(long cents) { this.cents = cents; return self(); }
        protected abstract B self();
    }
    static final class CardBuilder extends Builder<CardBuilder> {
        private String token = "";
        CardBuilder cardToken(String t) { token = t; return this; }
        @Override protected CardBuilder self() { return this; }
        String build() { return "card " + cents + " with " + token; }
    }

    public static void main(String[] args) {
        System.out.println(new PlainCardBuilder().cardToken("tok_1").amount(1_200).getClass().getSimpleName());
        System.out.println(new CardBuilder().amount(1_200).cardToken("tok_1").build());

        // Wrong move. Uncomment, predict the error, then run.
        // System.out.println(new PlainCardBuilder().amount(1_200).cardToken("tok_1").build());
    }
}
