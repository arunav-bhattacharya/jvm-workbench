package workbench.container.l01.demo;

import java.lang.reflect.Constructor;

/** The smallest container that works: read a constructor, build its parameters first, then call it. */
public class TinyContainerDemo {
    public static class FxRates {
        public FxRates() { System.out.println("  new FxRates"); }
    }

    public static class FeeCalculator {
        public FeeCalculator(FxRates rates) { System.out.println("  new FeeCalculator"); }
    }

    public static class QuoteService {
        public QuoteService(FxRates rates) { System.out.println("  new QuoteService"); }
    }

    public static class PaymentService {
        public PaymentService(FeeCalculator fees, QuoteService quotes) { System.out.println("  new PaymentService"); }
    }

    static Object build(Class<?> type) throws ReflectiveOperationException {
        Constructor<?> constructor = type.getConstructors()[0];          // 1. the recipe is the constructor
        Class<?>[] needs = constructor.getParameterTypes();
        Object[] args = new Object[needs.length];
        for (int i = 0; i < needs.length; i++) args[i] = build(needs[i]); // 2. build what it needs first
        return constructor.newInstance(args);                            // 3. then the object itself
    }

    public static void main(String[] args) throws Exception {
        System.out.println("by hand:");
        FxRates rates = new FxRates();
        new PaymentService(new FeeCalculator(rates), new QuoteService(rates));

        System.out.println("by reflection:");
        build(PaymentService.class);
    }
}
