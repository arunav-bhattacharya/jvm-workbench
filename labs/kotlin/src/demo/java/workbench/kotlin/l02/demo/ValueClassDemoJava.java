package workbench.kotlin.l02.demo;

/**
 * Java twin of ValueClassDemo.kt. Java has no value classes (Valhalla's are a JDK 28 preview), so it
 * sees what the bytecode holds: charge-<hash>(long), which javac can't call, and chargeFromJava(long).
 */
public class ValueClassDemoJava {

    // the closest Java shape today: a record, which is a real object with identity
    record CentsRecord(long value) {
        CentsRecord {
            if (value < 0) throw new IllegalArgumentException("negative amount: " + value);
        }
    }

    public static void main(String[] args) {
        System.out.println(ValueClassDemoKt.chargeFromJava(199L));
        // Java passes a raw long, so Cents' init block never runs:
        System.out.println(ValueClassDemoKt.chargeFromJava(-5L));
        System.out.println(new CentsRecord(199));

        // Wrong move. Uncomment, predict the error, then run.
        // System.out.println(ValueClassDemoKt.charge(199L));
    }
}
