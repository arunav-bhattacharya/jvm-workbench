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

    /** Runs one lighting or sound cue. No interface: a JDK proxy can't stand in for it. */
    public static class CueRunner {
        static int constructed;
        public CueRunner() { constructed++; }

        public String run(String cue) { return "ran " + cue + " (" + this.check(cue) + ")"; }  // self-call
        public String check(String cue) { return "checked " + cue; }
        public final String stage() { return "main stage"; }
    }

    /** Quarkus ArC style: the generated subclass instance IS the object; @SuperCall runs the original body on it. */
    public static class InSubclass {
        @RuntimeType
        public Object intercept(@Origin Method m, @SuperCall Callable<?> original) throws Exception {
            LOG.add("intercepted " + m.getName());
            return original.call();
        }
    }

    /** Spring AOP style: the generated subclass forwards to a separate target object. */
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
        Class<? extends CueRunner> sub = subclass(CueRunner.class, new InSubclass());
        System.out.println("generated " + sub.getName());
        System.out.println("declares  " + Arrays.stream(sub.getDeclaredMethods()).map(Method::getName).sorted().toList());

        CueRunner runner = sub.getDeclaredConstructor().newInstance();
        System.out.println(runner.run("LX-14") + ", on the " + runner.stage());
        System.out.println("subclass model:   " + LOG);
        LOG.clear();

        CueRunner.constructed = 0;
        CueRunner target = new CueRunner();
        CueRunner proxy = subclass(CueRunner.class, new Forwarding(target))
                .getDeclaredConstructor().newInstance();
        System.out.println(proxy.run("LX-15"));
        System.out.println("forwarding model: " + LOG + ", constructors run: " + CueRunner.constructed);

        try {
            new ByteBuddy().subclass(KotlinCueRunner.class).make();
        } catch (IllegalArgumentException e) {
            System.out.println("Kotlin class without open: " + e.getMessage());
        }
    }
}
