package workbench.concurrency.l11;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/** A record's fields are final. The objects they point to are not. */
public class ShallowRecord {
    record ShallowQuote(String pair, List<String> tiers, byte[] signature) {}

    record DeepQuote(String pair, List<String> tiers, byte[] signature) {
        DeepQuote {
            tiers = List.copyOf(tiers);                        // copy in
            signature = signature.clone();
        }

        @Override
        public byte[] signature() {
            return signature.clone();                          // copy out
        }
    }

    public static void main(String[] args) {
        List<String> tiers = new ArrayList<>(List.of("up to 10k at 1.0842"));
        byte[] sig = {7, 7, 7};
        ShallowQuote shallow = new ShallowQuote("EURUSD", tiers, sig);
        DeepQuote deep = new DeepQuote("EURUSD", tiers, sig);
        List<String> view = Collections.unmodifiableList(tiers);   // a read-only VIEW, not a copy

        tiers.add("above 10k at 9.9999");                      // the caller keeps changing its list...
        sig[0] = 0;                                            // ...and its array
        shallow.signature()[1] = 0;                            // a reader scribbles on what it was given
        deep.signature()[1] = 0;

        System.out.println("shallow: " + shallow.tiers() + "  signature " + Arrays.toString(shallow.signature()));
        System.out.println("deep:    " + deep.tiers() + "  signature " + Arrays.toString(deep.signature()));
        System.out.println("unmodifiableList view: " + view);
    }
}
