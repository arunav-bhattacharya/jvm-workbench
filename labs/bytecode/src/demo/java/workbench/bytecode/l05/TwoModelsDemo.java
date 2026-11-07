package workbench.bytecode.l05;

import net.bytebuddy.ByteBuddy;
import net.bytebuddy.implementation.MethodDelegation;
import net.bytebuddy.implementation.bind.annotation.AllArguments;
import net.bytebuddy.implementation.bind.annotation.Origin;
import net.bytebuddy.implementation.bind.annotation.RuntimeType;
import net.bytebuddy.implementation.bind.annotation.SuperCall;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.Callable;

import static net.bytebuddy.matcher.ElementMatchers.isDeclaredBy;
import static net.bytebuddy.matcher.ElementMatchers.named;

/** The same subclass proxy, two models: the proxy IS the object, or the proxy forwards to a target. */
public class TwoModelsDemo {
    static final List<String> LOG = new ArrayList<>();

    public static class SettlementService {
        static int constructed;
        public SettlementService() { constructed++; }

        public String settle(String batch) { return "settled " + batch + " (" + this.audit(batch) + ")"; }  // self-call
        public String audit(String batch) { return "audited " + batch; }
        public final String region() { return "eu-west"; }
    }

    /** ArC-style: the generated subclass instance is the bean; @SuperCall runs the original body on it. */
    public static class InSubclass {
        @RuntimeType
        public Object intercept(@Origin Method m, @SuperCall Callable<?> original) throws Exception {
            LOG.add("intercepted " + m.getName());
            return original.call();
        }
    }

    /** Spring-style: the generated subclass forwards to a separate target object. */
    public static class Forwarding {
        private final Object target;
        public Forwarding(Object target) { this.target = target; }

        @RuntimeType
        public Object intercept(@Origin Method m, @AllArguments Object[] args) throws Exception {
            LOG.add("forwarded " + m.getName());
            return m.invoke(target, args);
        }
    }

    static <T> Class<? extends T> subclass(Class<T> type, Object interceptor) {
        return new ByteBuddy().subclass(type)
                .method(isDeclaredBy(type))
                .intercept(MethodDelegation.withDefaultConfiguration()
                        .filter(named("intercept"))                 // bind to intercept() only, not equals() etc.
                        .to(interceptor))
                .make().load(type.getClassLoader()).getLoaded();
    }

    public static void main(String[] args) throws Exception {
        Class<? extends SettlementService> sub = subclass(SettlementService.class, new InSubclass());
        System.out.println("generated " + sub.getName());
        System.out.println("declares  " + Arrays.stream(sub.getDeclaredMethods()).map(Method::getName).sorted().toList());

        SettlementService bean = sub.getDeclaredConstructor().newInstance();
        System.out.println(bean.settle("B-17") + ", region " + bean.region());
        System.out.println("subclass model:   " + LOG);
        LOG.clear();

        SettlementService.constructed = 0;
        SettlementService target = new SettlementService();
        SettlementService proxy = subclass(SettlementService.class, new Forwarding(target))
                .getDeclaredConstructor().newInstance();
        System.out.println(proxy.settle("B-18"));
        System.out.println("forwarding model: " + LOG + ", constructors run: " + SettlementService.constructed);

        try {
            new ByteBuddy().subclass(KotlinFinalService.class).make();
        } catch (IllegalArgumentException e) {
            System.out.println("Kotlin class without open: " + e.getMessage());
        }
    }
}
