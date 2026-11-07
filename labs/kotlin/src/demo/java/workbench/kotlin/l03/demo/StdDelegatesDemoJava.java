package workbench.kotlin.l03.demo;

import java.util.Map;
import java.util.NoSuchElementException;

/**
 * Java twin of StdDelegatesDemo.kt. Java writes each behavior into the setter or getter by hand.
 */
public class StdDelegatesDemoJava {

    static final class PayoutJava {
        private String owner = "<none>";
        private int limit = 100;

        void setOwner(String owner) {
            String old = this.owner;
            this.owner = owner;                                   // observable: assign, then notify
            System.out.println("owner: " + old + " -> " + owner);
        }

        void setLimit(int limit) {
            if (limit <= 100) this.limit = limit;                 // vetoable: check, then assign
        }

        int getLimit() { return limit; }
    }

    static final class IssuerConfigJava {
        private final Map<String, Object> settings;
        IssuerConfigJava(Map<String, Object> settings) { this.settings = settings; }

        String host() { return (String) get("host"); }
        int port() { return (Integer) get("port"); }

        private Object get(String key) {
            if (!settings.containsKey(key)) throw new NoSuchElementException("Key " + key + " is missing in the map.");
            return settings.get(key);
        }
    }

    // provideDelegate has no Java twin: Java validates in the constructor, which also runs at build time
    static final class SettingsJava {
        final String issuerUrl;
        SettingsJava() {
            System.out.println("binding issuerUrl");
            issuerUrl = "value of issuerUrl";
        }
    }

    public static void main(String[] args) {
        PayoutJava p = new PayoutJava();
        p.setOwner("alice");
        p.setOwner("bob");
        p.setLimit(500);
        System.out.println("limit after veto: " + p.getLimit());
        p.setLimit(50);
        System.out.println("limit after ok: " + p.getLimit());

        IssuerConfigJava config = new IssuerConfigJava(Map.of("host", "issuer.example"));
        System.out.println("host = " + config.host());
        try {
            System.out.println("port = " + config.port());
        } catch (NoSuchElementException e) {
            System.out.println("port failed on access: " + e.getMessage());
        }

        System.out.println("building Settings...");
        SettingsJava s = new SettingsJava();
        System.out.println("built; issuerUrl = " + s.issuerUrl);
    }
}
