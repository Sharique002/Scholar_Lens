// cypress/support/commands.js

Cypress.Commands.add('resetDb', () => {
  const python = Cypress.env('PYTHON') || 'python';
  cy.exec(`"${python}" manage.py e2e_reset`, {
    env: {
      E2E: '1',
      DATABASE_URL: Cypress.env('E2E_DATABASE_URL'),
      E2E_PASSWORD: Cypress.env('E2E_PASSWORD'),
    },
    timeout: 120000,
  }).then((result) => {
    expect(result.code).to.eq(0);
  });
});

Cypress.Commands.add('loginAs', (role) => {
  const password = Cypress.env('E2E_PASSWORD') || 'TestPassword123!';
  const usernames = {
    student: 'e2e_student',
    faculty: 'e2e_faculty',
    custodian: 'e2e_custodian',
    office: 'e2e_office',
    dean: 'e2e_dean',
    biotech: 'e2e_biotech',
  };
  const username = usernames[role] || role;

  cy.session(
    role,
    () => {
      cy.visit('/accounts/login/');
      cy.get('input[name="username"]').type(username);
      cy.get('input[name="password"]').type(password);
      cy.get('button[type="submit"]').click();
      cy.url().should('include', '/dashboard/');
    },
    {
      validate() {
        cy.visit('/dashboard/');
        cy.get('aside.ums-sidebar').should('exist');
      },
    }
  );
});

Cypress.Commands.add('runCommand', (name, args = '') => {
  const python = Cypress.env('PYTHON') || 'python';
  const cmd = `"${python}" manage.py ${name} ${args}`.trim();
  return cy.exec(cmd, {
    env: {
      E2E: '1',
      DATABASE_URL: Cypress.env('E2E_DATABASE_URL'),
      E2E_PASSWORD: Cypress.env('E2E_PASSWORD'),
    },
    timeout: 60000,
  }).then((result) => {
    expect(result.code).to.eq(0);
    return result;
  });
});

Cypress.Commands.add('sidebar', () => {
  return cy.get('aside.ums-sidebar');
});
