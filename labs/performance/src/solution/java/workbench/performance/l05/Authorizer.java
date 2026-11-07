package workbench.performance.l05;

public final class Authorizer {
    private final Issuer issuer;

    public Authorizer(Issuer issuer) {
        this.issuer = issuer;
    }

    public boolean authorize(String merchant, long amountCents) {
        AuthorizationEvent event = new AuthorizationEvent();
        event.begin();                                   // 1. start the clock
        boolean approved = issuer.approve(merchant, amountCents);
        event.end();                                     // 2. stop it: the duration is the issuer call
        if (event.shouldCommit()) {                      // 3. false when no recording wants this event
            event.merchant = merchant;
            event.amountCents = amountCents;
            event.approved = approved;
            event.commit();                              // 4. write it into the recording's buffers
        }
        return approved;
    }
}
