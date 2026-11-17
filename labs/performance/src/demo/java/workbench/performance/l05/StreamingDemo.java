package workbench.performance.l05;

import jdk.jfr.consumer.RecordingStream;

import java.time.Duration;

/** Watches the running JVM with JFR event streaming: slow store calls and garbage collections, live. */
public class StreamingDemo {
    public static void main(String[] args) throws Exception {
        try (RecordingStream rs = new RecordingStream()) {
            rs.enable("workbench.StoreCall").withThreshold(Duration.ofMillis(35));   // only the slow ones
            rs.enable("jdk.GarbageCollection");
            rs.onEvent("workbench.StoreCall", e -> System.out.printf("slow store call: %s, %d ms%n",
                    e.getString("shelf"), e.getDuration().toMillis()));
            rs.onEvent("jdk.GarbageCollection", e -> System.out.printf("GC: %s, %.1f ms pause total%n",
                    e.getString("name"), e.getDuration("sumOfPauses").toNanos() / 1e6));
            rs.startAsync();                     // events arrive on a background thread
            ReportWorkload.run(3);
            Thread.sleep(1_500);                 // let the last flush reach us
        }
    }
}
