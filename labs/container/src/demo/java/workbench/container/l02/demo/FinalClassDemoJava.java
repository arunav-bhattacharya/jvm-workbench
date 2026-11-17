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
    public static final class FinalPrices {
        @Timed
        public long feeCents(long priceCents) { return (priceCents * 29 + 500) / 1000; }
    }

    @Component
    public static class OpenPrices {
        @Timed
        public long feeCents(long priceCents) { return (priceCents * 29 + 500) / 1000; }
    }

    public static void main(String[] args) throws Exception {
        for (Class<?> type : List.of(FinalPrices.class, OpenPrices.class)) {
            Method fee = type.getMethod("feeCents", long.class);
            System.out.printf("%s: class final=%s, feeCents final=%s%n", type.getSimpleName(),
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
            new ByteBuddy().subclass(FinalPrices.class).make();               // what you get without the check
        } catch (IllegalArgumentException e) {
            System.out.println("Byte Buddy on its own: " + e.getMessage());
        }
    }
}
