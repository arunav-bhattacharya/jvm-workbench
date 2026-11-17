package workbench.kotlin.l03.demo;

import java.util.Map;
import java.util.NoSuchElementException;

/**
 * Java twin of StdDelegatesDemo.kt. Java writes each behavior into the setter or getter by hand.
 */
public class StdDelegatesDemoJava {

    static final class PrintRequestJava {
        private String owner = "<none>";
        private int copies = 1;

        void setOwner(String owner) {
            String old = this.owner;
            this.owner = owner;                                   // observable: assign, then notify
            System.out.println("owner: " + old + " -> " + owner);
        }

        void setCopies(int copies) {
            if (copies <= 100) this.copies = copies;              // vetoable: check, then assign
        }

        int getCopies() { return copies; }
    }

    static final class PrinterConfigJava {
        private final Map<String, Object> settings;
        PrinterConfigJava(Map<String, Object> settings) { this.settings = settings; }

        String host() { return (String) get("host"); }
        int port() { return (Integer) get("port"); }

        private Object get(String key) {
            if (!settings.containsKey(key)) throw new NoSuchElementException("Key " + key + " is missing in the map.");
            return settings.get(key);
        }
    }

    // provideDelegate has no Java twin: Java validates in the constructor, which also runs at build time
    static final class ShopSettingsJava {
        final String printerHost;
        ShopSettingsJava() {
            System.out.println("binding printerHost");
            printerHost = "value of printerHost";
        }
    }

    public static void main(String[] args) {
        PrintRequestJava request = new PrintRequestJava();
        request.setOwner("alice");
        request.setOwner("bob");
        request.setCopies(500);
        System.out.println("copies after veto: " + request.getCopies());
        request.setCopies(50);
        System.out.println("copies after ok: " + request.getCopies());

        PrinterConfigJava config = new PrinterConfigJava(Map.of("host", "laser-1.local"));
        System.out.println("host = " + config.host());
        try {
            System.out.println("port = " + config.port());
        } catch (NoSuchElementException e) {
            System.out.println("port failed on access: " + e.getMessage());
        }

        System.out.println("building ShopSettings...");
        ShopSettingsJava s = new ShopSettingsJava();
        System.out.println("built; printerHost = " + s.printerHost);
    }
}
