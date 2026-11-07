package workbench.bytecode.l07;

import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.Instrumentation;
import java.security.ProtectionDomain;
import java.util.concurrent.atomic.AtomicInteger;

/** A startup agent: the JVM calls premain before main. It watches classes load and changes nothing. */
public class CountingAgent {
    public static void premain(String args, Instrumentation inst) {
        System.out.println("[agent] premain args=" + args + ", classes already loaded: " + inst.getAllLoadedClasses().length);
        AtomicInteger seen = new AtomicInteger();
        inst.addTransformer(new ClassFileTransformer() {
            @Override
            public byte[] transform(ClassLoader loader, String className, Class<?> classBeingRedefined,
                                    ProtectionDomain domain, byte[] classfileBuffer) {
                seen.incrementAndGet();
                if (className != null && className.startsWith("workbench/")) {
                    System.out.println("[agent] loading " + className + " (" + classfileBuffer.length + " bytes)");
                }
                return null;                       // null means "no change"
            }
        });
        Runtime.getRuntime().addShutdownHook(new Thread(() ->
                System.out.println("[agent] transformer saw " + seen.get() + " class definitions")));
    }
}
