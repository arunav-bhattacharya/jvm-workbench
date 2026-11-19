package workbench.ksp.app.l09;

import java.lang.management.ClassLoadingMXBean;
import java.lang.management.ManagementFactory;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

// The Java twin of CardTiming.kt: Java code calling the cards KSP generated in Kotlin. They compiled to ordinary
// classes, so Java sees MovingDayList as a class with an INSTANCE field, and the reflection cards as static methods.
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l09.CardTimingJava
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l09.CardTimingJava -Pargs=reflection-first
public class CardTimingJava {
    public static void main(String[] args) {
        Map<String, Function<Object, String>> ways = new LinkedHashMap<>();
        ways.put("generated", MovingDayList.INSTANCE::cardFor);
        ways.put("reflection", ReflectionCardsKt::reflectionCard);
        ways.put("cached", CachedReflectionCards.INSTANCE::card);
        List<Object> things = MoveMateKt.movingDayThings();
        Object lamp = things.get(1);

        List<String> order = args.length > 0 && args[0].equals("reflection-first")
                ? List.of("reflection", "generated") : List.of("generated", "reflection");
        ClassLoadingMXBean classes = ManagementFactory.getClassLoadingMXBean();
        for (String name : order) {
            long loadedBefore = classes.getTotalLoadedClassCount();
            long start = System.nanoTime();
            String card = ways.get(name).apply(lamp);
            double ms = (System.nanoTime() - start) / 1e6;
            System.out.printf("first call, %-10s %6.2f ms, %3d classes loaded -> %s%n",
                    name + ":", ms, classes.getTotalLoadedClassCount() - loadedBefore, card);
        }

        boolean agree = things.stream().allMatch(t -> ways.values().stream().map(f -> f.apply(t)).distinct().count() == 1);
        System.out.println("all three ways agree on all " + things.size() + " cards: " + agree);

        int calls = 1_000_000;
        for (var entry : ways.entrySet()) {
            Function<Object, String> f = entry.getValue();
            for (int i = 0; i < 200_000; i++) f.apply(things.get(i % 4));
            StringBuilder rounds = new StringBuilder();
            for (int r = 0; r < 3; r++) {
                long length = 0;
                long t0 = System.nanoTime();
                for (int i = 0; i < calls; i++) length += f.apply(things.get(i % 4)).length();
                if (length == 0) throw new IllegalStateException();
                rounds.append(r == 0 ? "" : " / ").append(String.format("%.0f", (System.nanoTime() - t0) / (double) calls));
            }
            System.out.printf("%-12s %s ns per card%n", entry.getKey(), rounds);
        }
    }
}
