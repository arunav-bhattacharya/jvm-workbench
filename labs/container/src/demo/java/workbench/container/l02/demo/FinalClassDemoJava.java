package workbench.container.l02.demo;

import net.bytebuddy.ByteBuddy;
import workbench.container.l02.Component;
import workbench.container.l02.Container;
import workbench.container.l02.ContainerException;
import workbench.container.l02.Timed;

import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.List;

/** Two Java classes with the same @Timed method. Java classes are open unless you write final. */
public class FinalClassDemoJava {
    @Component
    public static final class FinalFees {
        @Timed
        public long feeMinor(long amountMinor) { return (amountMinor * 29 + 500) / 1000; }
    }

    @Component
    public static class OpenFees {
        @Timed
        public long feeMinor(long amountMinor) { return (amountMinor * 29 + 500) / 1000; }
    }

    public static void main(String[] args) throws Exception {
        for (Class<?> type : List.of(FinalFees.class, OpenFees.class)) {
            Method fee = type.getMethod("feeMinor", long.class);
            System.out.printf("%s: class final=%s, feeMinor final=%s%n", type.getSimpleName(),
                    Modifier.isFinal(type.getModifiers()), Modifier.isFinal(fee.getModifiers()));
            try {
                Container c = new Container(List.of(type));
                Object bean = c.get(type);
                fee.invoke(bean, 12_000L);
                System.out.println("  wired as " + bean.getClass().getSimpleName() + ", timed calls " + c.callLog().names());
            } catch (ContainerException e) {
                System.out.println("  refused: " + e.getMessage());
            }
        }
        try {
            new ByteBuddy().subclass(FinalFees.class).make();               // what you get without the check
        } catch (IllegalArgumentException e) {
            System.out.println("Byte Buddy on its own: " + e.getMessage());
        }
    }
}
