package workbench.bytecode.l03;

import java.lang.invoke.CallSite;
import java.lang.invoke.LambdaMetafactory;
import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;
import java.lang.invoke.StringConcatFactory;
import java.util.function.Supplier;

import static java.lang.invoke.MethodType.methodType;

/** The two bootstrap calls javac's invokedynamic would make, made by hand. */
public class ByHandDemo {
    static String banner() { return "settlement batch 42"; }

    @SuppressWarnings("unchecked")
    public static void main(String[] args) throws Throwable {
        MethodHandles.Lookup lookup = MethodHandles.lookup();

        // 1. () -> banner() as a Supplier<String>
        CallSite site = LambdaMetafactory.metafactory(
                lookup,
                "get",                                              // the interface method's name
                methodType(Supplier.class),                         // factory type: captures nothing
                methodType(Object.class),                           // Supplier.get() after erasure
                lookup.findStatic(ByHandDemo.class, "banner", methodType(String.class)),
                methodType(String.class));                          // get() as this lambda returns it
        Supplier<String> s = (Supplier<String>) site.getTarget().invoke();
        System.out.println(s.get() + "  <- " + s.getClass().getName() + ", call site: " + site.getClass().getSimpleName());

        // 2. "batch " + id + " has " + count + " payments"
        CallSite concat = StringConcatFactory.makeConcatWithConstants(
                lookup, "concat", methodType(String.class, int.class, long.class),
                "batch \u0001 has \u0001 payments");
        MethodHandle mh = concat.getTarget();
        System.out.println((String) mh.invokeExact(42, 1_250L) + "  <- call site: " + concat.getClass().getSimpleName());
    }
}
