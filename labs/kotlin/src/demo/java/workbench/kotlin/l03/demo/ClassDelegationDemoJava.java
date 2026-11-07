package workbench.kotlin.l03.demo;

/**
 * Java twin of ClassDelegationDemo.kt. Java has no `by`, so you write the forwarding yourself.
 * Written by hand, it reads the field on every call, so swapping the policy works.
 */
public class ClassDelegationDemoJava {

    static final class ConfigurableFeesJava implements FeePolicy {
        private FeePolicy policy;

        ConfigurableFeesJava(FeePolicy policy) { this.policy = policy; }

        void setPolicy(FeePolicy policy) { this.policy = policy; }

        @Override
        public long feeMinor(long amountMinor) {
            return policy.feeMinor(amountMinor);         // reads the current field each time
        }
    }

    public static void main(String[] args) {
        ConfigurableFeesJava fees = new ConfigurableFeesJava(new FlatFee(25));
        System.out.println("fee: " + fees.feeMinor(10_000));
        fees.setPolicy(new FlatFee(99));
        System.out.println("after swap, fee: " + fees.feeMinor(10_000));

        // the Kotlin class, seen from Java: setPolicy changes the property, not the $$delegate_0 field
        ConfigurableFees kotlinFees = new ConfigurableFees(new FlatFee(25));
        kotlinFees.setPolicy(new FlatFee(99));
        System.out.println("Kotlin class after swap, fee: " + kotlinFees.feeMinor(10_000));
    }
}
