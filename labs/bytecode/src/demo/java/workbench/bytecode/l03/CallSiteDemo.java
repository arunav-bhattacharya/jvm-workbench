package workbench.bytecode.l03;

import java.lang.invoke.ConstantCallSite;
import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;
import java.lang.invoke.MutableCallSite;

/** A call site is a slot holding a target method handle. invokedynamic calls through one. */
public class CallSiteDemo {
    static String eur(long minor) { return String.format("%d.%02d EUR", minor / 100, minor % 100); }
    static String usd(long minor) { return String.format("$%d.%02d", minor / 100, minor % 100); }

    public static void main(String[] args) throws Throwable {
        MethodHandles.Lookup lookup = MethodHandles.lookup();
        MethodType type = MethodType.methodType(String.class, long.class);
        MethodHandle eur = lookup.findStatic(CallSiteDemo.class, "eur", type);
        MethodHandle usd = lookup.findStatic(CallSiteDemo.class, "usd", type);

        MutableCallSite site = new MutableCallSite(eur);
        MethodHandle invoker = site.dynamicInvoker();   // what an invokedynamic instruction would call through
        System.out.println("linked to eur: " + (String) invoker.invokeExact(362_550L));
        site.setTarget(usd);                            // relink: same invoker, new target
        System.out.println("relinked to usd: " + (String) invoker.invokeExact(362_550L));

        ConstantCallSite fixed = new ConstantCallSite(eur);   // what lambdas and string concatenation get
        try {
            fixed.setTarget(usd);
        } catch (UnsupportedOperationException e) {
            System.out.println("ConstantCallSite.setTarget -> UnsupportedOperationException: linked for good");
        }
    }
}
