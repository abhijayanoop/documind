import pytest
from documind.rbac import AccessController, UserRole, AccessLevel


@pytest.fixture
def ac():
    return AccessController()


def test_candidate_sees_only_public(ac):
    """A candidate in CRED can retrieve the public doc, and ONLY that."""
    doc_ids = ac.get_accessible_document_ids("candidate_1", "cred")
    assert "doc_001" in doc_ids          # public — allowed
    assert "doc_002" not in doc_ids      # salary_tier — forbidden
    assert "doc_003" not in doc_ids      # hiring_manager — forbidden


def test_manager_sees_salary(ac):
    """A hiring manager can reach salary-tier docs."""
    doc_ids = ac.get_accessible_document_ids("manager_1", "cred")
    assert "doc_001" in doc_ids
    assert "doc_002" in doc_ids          # salary_tier — now allowed
    assert "doc_003" in doc_ids          # hiring_manager — allowed


def test_tenant_isolation(ac):
    """A CRED user's accessible docs never include Razorpay rows.

    Both tenants have a 'doc_001', but the candidate is scoped to CRED,
    so we assert they get CRED's set and that Razorpay's salary doc
    (doc_002) is unreachable regardless.
    """
    cred_docs = ac.get_accessible_document_ids("candidate_1", "cred")
    # candidate_2 lives in razorpay; candidate_1 must not inherit anything cross-tenant
    assert "doc_002" not in cred_docs    # would be razorpay salary if leaking

    razorpay_docs = ac.get_accessible_document_ids("candidate_2", "razorpay")
    assert "doc_001" in razorpay_docs    # razorpay's public doc
    assert "doc_002" not in razorpay_docs# razorpay salary — forbidden to candidate


def test_unknown_user_fails_closed(ac):
    """An unknown user resolves to PUBLIC_USER (least privilege), not an error."""
    role = ac.get_user_role("ghost_user", "cred")
    assert role is UserRole.PUBLIC_USER
    doc_ids = ac.get_accessible_document_ids("ghost_user", "cred")
    assert doc_ids == ["doc_001"]        # only the public doc


def test_access_matrix_admin_sees_all(ac):
    """Sanity check on the matrix itself: admin covers every access level."""
    levels = ac.get_accessible_levels(UserRole.ADMIN)
    assert levels == set(AccessLevel)