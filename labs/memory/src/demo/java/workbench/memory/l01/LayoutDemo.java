package workbench.memory.l01;

import com.sun.management.ThreadMXBean;
import org.openjdk.jol.datamodel.Model64_Lilliput;
import org.openjdk.jol.info.ClassLayout;
import org.openjdk.jol.info.GraphLayout;
import org.openjdk.jol.layouters.HotSpotLayouter;
import workbench.memory.Jvm;

import java.lang.management.ManagementFactory;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Prints real object layouts with JOL. Pass JVM flags to see them change, for example
 * -Pargs=-XX:-UseCompressedOops (the demo then reruns itself in a child JVM with those flags).
 */
public class LayoutDemo {
    static class Payment {
        boolean captured;
        long amountMinor;
        byte status;
        String currency;
        int attempts;
        Object metadata;
    }

    public static void main(String[] args) {
        if (args.length > 0) {                                   // flags given: rerun in a JVM that has them
            Jvm.run(Arrays.asList(args), LayoutDemo.class.getName());
            return;
        }
        System.out.println(ClassLayout.parseClass(Payment.class).toPrintable());

        List<Integer> boxed = new ArrayList<>();
        for (int i = 0; i < 1_000; i++) boxed.add(i);
        System.out.printf("Object %d, Integer %d, Long %d, String shell %d bytes%n",
                ClassLayout.parseClass(Object.class).instanceSize(), ClassLayout.parseClass(Integer.class).instanceSize(),
                ClassLayout.parseClass(Long.class).instanceSize(), ClassLayout.parseClass(String.class).instanceSize());
        System.out.printf("\"EUR\" with its byte[]: %d bytes%n", GraphLayout.parseInstance(new String("EUR")).totalSize());
        System.out.printf("ArrayList<Integer> of 0..999: %,d bytes, int[1000]: %,d bytes%n",
                GraphLayout.parseInstance(boxed).totalSize(), GraphLayout.parseInstance((Object) new int[1_000]).totalSize());

        // JOL can also simulate a layout: here, an 8-byte compact header with compressed references
        ClassLayout compact = ClassLayout.parseClass(Payment.class, new HotSpotLayouter(new Model64_Lilliput(true, 8, false), 25));
        System.out.printf("Payment with compact headers (JOL simulation): %d bytes%n", compact.instanceSize());

        // and the JVM itself can tell you: count the bytes 10,000 new Payment objects take
        ThreadMXBean threads = (ThreadMXBean) ManagementFactory.getThreadMXBean();
        Payment[] keep = new Payment[10_000];                     // allocate the array before we start counting
        long before = threads.getCurrentThreadAllocatedBytes();
        for (int i = 0; i < keep.length; i++) keep[i] = new Payment();
        long bytes = threads.getCurrentThreadAllocatedBytes() - before;
        System.out.printf("10,000 Payments allocated %,d bytes: %d per object in this JVM%n", bytes, bytes / keep.length);
    }
}
