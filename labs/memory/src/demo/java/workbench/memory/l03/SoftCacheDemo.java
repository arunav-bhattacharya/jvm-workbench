package workbench.memory.l03;

import workbench.memory.Jvm;

import java.lang.ref.SoftReference;
import java.util.List;

/** A 40 MB decoded photo behind a soft reference in a 64 MB heap, then another 40 MB allocation. Runs in a child JVM. */
public class SoftCacheDemo {
    public static void main(String[] args) {
        if (args.length == 0) {
            Jvm.run(List.of("-Xmx64m", "-Xlog:gc"), SoftCacheDemo.class.getName(), "run");
            return;
        }
        SoftReference<byte[]> beach = new SoftReference<>(new byte[40 << 20]);   // a decoded photo, kept "if there's room"
        System.out.println("beach photo cached: " + (beach.get() != null));
        byte[] dog = new byte[40 << 20];                   // only fits if the GC clears the soft reference
        System.out.println("after decoding a 40 MB dog photo: beach photo cached: " + (beach.get() != null) + ", dog " + dog.length + " bytes");
    }
}
