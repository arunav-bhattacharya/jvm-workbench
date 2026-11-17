package workbench.kotlin.l02.demo;

/**
 * Java twin of ValueClassDemo.kt. Java has no value classes (Valhalla's are a JDK 28 preview), so it
 * sees what the bytecode holds: ship-<hash>(long), which javac can't call, and shipFromJava(long).
 */
public class ValueClassDemoJava {

    // the closest Java shape today: a record, which is a real object with identity
    record GramsRecord(long value) {
        GramsRecord {
            if (value < 0) throw new IllegalArgumentException("negative weight: " + value);
        }
    }

    public static void main(String[] args) {
        System.out.println(ValueClassDemoKt.shipFromJava(199L));
        // Java passes a raw long, so Grams' init block never runs:
        System.out.println(ValueClassDemoKt.shipFromJava(-5L));
        System.out.println(new GramsRecord(199));

        // Wrong move. Uncomment, predict the error, then run.
        // System.out.println(ValueClassDemoKt.ship(199L));
    }
}
