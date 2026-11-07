// A client compiled against version 1, then run against version 2 without being recompiled.
//
// Run from labs/modernjava/javac/remainder:
//   javac -d ../../build/remainder v1/*.java Client.java      # 1. compile everything against v1
//   java -cp ../../build/remainder Client                     # 2. works
//   javac -d ../../build/remainder v2/*.java                  # 3. recompile only the hierarchy, now v2
//   java -cp ../../build/remainder Client                     # 4. the old Client meets Frozen and CRITICAL
//   javac -cp ../../build/remainder -d ../../build/remainder Client.java   # 5. recompile Client: errors
public class Client {

    static String label(Status s) {
        return switch (s) {                       // exhaustive for v1, no default
            case Active a -> "active";
            case Closed c -> "closed";
        };
    }

    static int priority(Level l) {
        return switch (l) {                       // exhaustive for v1, no default
            case LOW -> 1;
            case HIGH -> 2;
        };
    }

    public static void main(String[] args) throws Exception {
        System.out.println(label(new Active("a1")) + ", priority " + priority(Level.LOW));

        // the newest values this JVM knows about, found by name because v1 had no such names
        Level last = Level.values()[Level.values().length - 1];
        Status newest = Class.forName(Status.class.getPermittedSubclasses().length > 2 ? "Frozen" : "Closed")
                .asSubclass(Status.class).getDeclaredConstructor(String.class).newInstance("x9");
        try {
            System.out.println("sealed switch: " + label(newest));
        } catch (MatchException e) {
            System.out.println("sealed switch: " + e);
        }
        try {
            System.out.println("enum switch:   priority " + priority(last));
        } catch (MatchException e) {
            System.out.println("enum switch:   " + e);
        }
    }
}
