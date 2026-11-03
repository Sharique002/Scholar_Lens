describe('13 - Automated Accessibility Audit (Axe Core)', () => {
  before(() => {
    cy.resetDb();
  });

  const checkA11yForPage = (url, user = 'student') => {
    if (user) {
      cy.loginAs(user);
    }
    cy.visit(url);
    cy.injectAxe();
    cy.checkA11y(
      null,
      {
        includedImpacts: ['critical', 'serious'],
      },
      (violations) => {
        if (violations.length) {
          const violationData = violations.map(({ id, impact, description, nodes }) => ({
            id,
            impact,
            description,
            targets: nodes.map(n => n.target),
            htmls: nodes.map(n => n.html),
            summaries: nodes.map(n => n.failureSummary),
          }));
          cy.task('log', JSON.stringify(violationData, null, 2));
        }
      }
    );
  };

  it('audits Landing Page', () => {
    checkA11yForPage('/', null);
  });

  it('audits Sign In Page', () => {
    checkA11yForPage('/accounts/login/', null);
  });

  it('audits Dashboard', () => {
    checkA11yForPage('/dashboard/');
  });

  it('audits Papers List', () => {
    checkA11yForPage('/papers/');
  });

  it('audits Facility Detail Page', () => {
    checkA11yForPage('/facilities/1/');
  });

  it('audits Facility Booking Form', () => {
    checkA11yForPage('/facilities/1/book/');
  });

  it('audits Funding Calls Register', () => {
    checkA11yForPage('/funding/');
  });

  it('audits Project Milestones Timeline', () => {
    checkA11yForPage('/projects/1/milestones/', 'faculty');
  });

  it('audits Research Openings Board', () => {
    checkA11yForPage('/opportunities/');
  });

  it('audits Expertise Search', () => {
    checkA11yForPage('/search/expertise/');
  });

  it('audits Institutional Research Report', () => {
    checkA11yForPage('/analytics/research/', 'dean');
  });
});
