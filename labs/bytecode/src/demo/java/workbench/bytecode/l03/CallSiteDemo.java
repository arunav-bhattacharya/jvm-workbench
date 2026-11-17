package workbench.bytecode.l03;

import java.lang.invoke.ConstantCallSite;
import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;
import java.lang.invoke.MutableCallSite;

/** A call site is a slot holding a target method handle. invokedynamic calls through one. */
public class CallSiteDemo {
    static String inSeconds(long s) { return s + " seconds"; }
    static String inMinutes(long s) { return s / 60 + " minutes"; }

    public static void main(String[] args) throws Throwable {
        MethodHandles.Lookup lookup = MethodHandles.lookup();
        MethodType type = MethodType.methodType(String.class, long.class);
        MethodHandle inSeconds = lookup.findStatic(CallSiteDemo.class, "inSeconds", type);
        MethodHandle inMinutes = lookup.findStatic(CallSiteDemo.class, "inMinutes", type);

        MutableCallSite site = new MutableCallSite(inSeconds);
        MethodHandle invoker = site.dynamicInvoker();   // what an invokedynamic instruction would call through
        System.out.println("linked to inSeconds: " + (String) invoker.invokeExact(120L));
        site.setTarget(inMinutes);                      // relink: same invoker, new target
        System.out.println("relinked to inMinutes: " + (String) invoker.invokeExact(120L));

        ConstantCallSite fixed = new ConstantCallSite(inSeconds);   // what lambdas and string concatenation get
        try {
            fixed.setTarget(inMinutes);
        } catch (UnsupportedOperationException e) {
            System.out.println("ConstantCallSite.setTarget -> UnsupportedOperationException: linked for good");
        }
    }
}
