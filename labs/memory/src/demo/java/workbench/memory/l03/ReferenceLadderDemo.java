package workbench.memory.l03;

import java.lang.ref.PhantomReference;
import java.lang.ref.Reference;
import java.lang.ref.ReferenceQueue;
import java.lang.ref.SoftReference;
import java.lang.ref.WeakReference;

/** One object on each rung of the reachability ladder, before and after a GC. */
public class ReferenceLadderDemo {
    public static void main(String[] args) throws InterruptedException {
        ReferenceQueue<byte[]> queue = new ReferenceQueue<>();
        byte[] strong = new byte[1_000];                                  // a plain local: strongly reachable
        SoftReference<byte[]> soft = new SoftReference<>(new byte[1_000], queue);
        WeakReference<byte[]> weak = new WeakReference<>(new byte[1_000], queue);
        PhantomReference<byte[]> phantom = new PhantomReference<>(new byte[1_000], queue);

        System.out.printf("before GC: soft %s, weak %s, phantom.get() %s%n", soft.get() != null, weak.get() != null, phantom.get());
        System.gc();                                                      // a request; fine in a demo, never a guarantee
        System.out.printf("after GC:  soft %s, weak %s, phantom.get() %s%n", soft.get() != null, weak.get() != null, phantom.get());
        for (Reference<?> r; (r = queue.remove(500)) != null; ) {
            System.out.println("enqueued: " + r.getClass().getSimpleName());
        }
        Reference.reachabilityFence(strong);                              // keep `strong` alive until here
        System.out.println("strong array still here: " + strong.length + " bytes");
    }
}
