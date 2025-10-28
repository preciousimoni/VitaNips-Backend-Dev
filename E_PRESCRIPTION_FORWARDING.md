# E-Prescription Forwarding Feature

## Overview
This feature allows patients to forward their prescriptions from completed appointments directly to pharmacies of their choice. The system creates a medication order at the pharmacy and notifies both the patient and pharmacy.

## Implementation Status: ✅ Backend Complete | ⚠️ Frontend Pending

---

## Backend Implementation

### API Endpoint
**POST** `/api/doctors/prescriptions/<prescription_id>/forward/`

#### Request
```json
{
  "pharmacy_id": 123
}
```

#### Success Response (201 Created)
```json
{
  "message": "Prescription successfully forwarded to Pharmacy Name.",
  "order": {
    "id": 456,
    "user": 1,
    "pharmacy": {
      "id": 123,
      "name": "Pharmacy Name",
      "address": "123 Main St",
      "phone_number": "+1234567890",
      "email": "pharmacy@example.com"
    },
    "prescription": {
      "id": 789,
      "appointment": 101,
      "doctor": "Dr. Smith",
      "diagnosis": "Common cold",
      "notes": "Take with food"
    },
    "status": "pending",
    "items": [
      {
        "id": 1,
        "medication_name_text": "Amoxicillin",
        "dosage_text": "500mg",
        "quantity": 1
      }
    ],
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

#### Error Responses

**400 Bad Request**
```json
{
  "error": "pharmacy_id is required."
}
```
```json
{
  "error": "Cannot forward prescription. The appointment must be completed first. Current status: scheduled."
}
```
```json
{
  "error": "Prescription has no items to order."
}
```

**404 Not Found**
```json
{
  "error": "Prescription not found or you don't have permission to access it."
}
```
```json
{
  "error": "Pharmacy not found or is inactive."
}
```

**409 Conflict** (Duplicate Order)
```json
{
  "error": "An order for this prescription already exists.",
  "order_id": 456,
  "pharmacy": "Pharmacy Name",
  "status": "pending"
}
```

**500 Internal Server Error**
```json
{
  "error": "An error occurred while creating the order. Please try again."
}
```

---

## Validation & Business Logic

### Pre-Flight Checks
1. **Authentication**: User must be logged in
2. **Ownership**: User must own the prescription
3. **Appointment Status**: Associated appointment must be "completed"
4. **Pharmacy Status**: Pharmacy must exist and be active
5. **Duplicate Prevention**: No existing order for this prescription
6. **Prescription Items**: Prescription must have at least one item

### Transaction Safety
- Uses Django's `transaction.atomic()` to ensure data consistency
- All order creation steps (order + items + notification) succeed or fail together
- Rollback on any error prevents partial data

### Notifications
- Patient receives in-app notification: "Your prescription has been forwarded to [Pharmacy]. Order #[ID] is being processed."
- Notification includes link to order details: `/orders/{order_id}`

### Logging
- Success: `Prescription {id} forwarded to pharmacy {id} by user {id}. Order {id} created.`
- Error: `Error forwarding prescription {id}: {error_message}`

---

## Database Models

### MedicationOrder
```python
user: ForeignKey(User)
pharmacy: ForeignKey(Pharmacy)
prescription: ForeignKey(Prescription, null=True)
status: CharField(choices=['pending', 'confirmed', 'ready', 'delivered', 'cancelled'])
notes: TextField
created_at: DateTimeField(auto_now_add=True)
```

### MedicationOrderItem
```python
order: ForeignKey(MedicationOrder)
prescription_item: ForeignKey(PrescriptionItem, null=True)
medication_name_text: CharField
dosage_text: CharField
quantity: IntegerField(default=1)
```

---

## Frontend Integration (TODO)

### Step 1: Create API Function
**File**: `VitaNips-Frontend-Dev/src/api/prescriptions.ts`

```typescript
import api from './config';

export interface ForwardPrescriptionRequest {
  pharmacy_id: number;
}

export interface ForwardPrescriptionResponse {
  message: string;
  order: {
    id: number;
    user: number;
    pharmacy: {
      id: number;
      name: string;
      address: string;
      phone_number: string;
      email: string;
    };
    prescription: any;
    status: string;
    items: Array<{
      id: number;
      medication_name_text: string;
      dosage_text: string;
      quantity: number;
    }>;
    created_at: string;
  };
}

export const forwardPrescriptionToPharmacy = async (
  prescriptionId: number,
  data: ForwardPrescriptionRequest
): Promise<ForwardPrescriptionResponse> => {
  const response = await api.post(
    `/doctors/prescriptions/${prescriptionId}/forward/`,
    data
  );
  return response.data;
};
```

### Step 2: Create Pharmacy Selection Modal Component
**File**: `VitaNips-Frontend-Dev/src/components/PharmacySelectionModal.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import { XMarkIcon, MagnifyingGlassIcon, MapPinIcon } from '@heroicons/react/24/outline';
import { getPharmacies } from '../api/pharmacy';

interface Pharmacy {
  id: number;
  name: string;
  address: string;
  phone_number: string;
  distance?: number;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (pharmacyId: number) => void;
  loading?: boolean;
}

export const PharmacySelectionModal: React.FC<Props> = ({
  isOpen,
  onClose,
  onSelect,
  loading = false,
}) => {
  const [pharmacies, setPharmacies] = useState<Pharmacy[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [fetching, setFetching] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchPharmacies();
    }
  }, [isOpen]);

  const fetchPharmacies = async () => {
    setFetching(true);
    try {
      const data = await getPharmacies({ search: searchQuery });
      setPharmacies(data.results || data);
    } catch (error) {
      console.error('Failed to fetch pharmacies:', error);
    } finally {
      setFetching(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchPharmacies();
  };

  const handleSelect = () => {
    if (selectedId) {
      onSelect(selectedId);
    }
  };

  const filteredPharmacies = searchQuery
    ? pharmacies.filter((p) =>
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.address.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : pharmacies;

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/30" aria-hidden="true" />
      
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="mx-auto max-w-2xl w-full bg-white rounded-xl shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between border-b px-6 py-4">
            <Dialog.Title className="text-lg font-semibold text-gray-900">
              Select Pharmacy
            </Dialog.Title>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Search */}
          <div className="px-6 py-4 border-b">
            <form onSubmit={handleSearch} className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search pharmacies by name or location..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </form>
          </div>

          {/* Pharmacy List */}
          <div className="px-6 py-4 max-h-96 overflow-y-auto">
            {fetching ? (
              <div className="text-center py-8 text-gray-500">
                Loading pharmacies...
              </div>
            ) : filteredPharmacies.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No pharmacies found. Try adjusting your search.
              </div>
            ) : (
              <div className="space-y-2">
                {filteredPharmacies.map((pharmacy) => (
                  <div
                    key={pharmacy.id}
                    onClick={() => setSelectedId(pharmacy.id)}
                    className={`p-4 border rounded-lg cursor-pointer transition ${
                      selectedId === pharmacy.id
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-primary-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">
                          {pharmacy.name}
                        </h3>
                        <div className="flex items-center mt-1 text-sm text-gray-500">
                          <MapPinIcon className="h-4 w-4 mr-1" />
                          {pharmacy.address}
                        </div>
                        <p className="mt-1 text-sm text-gray-600">
                          {pharmacy.phone_number}
                        </p>
                      </div>
                      {pharmacy.distance && (
                        <span className="text-sm text-gray-500 ml-4">
                          {pharmacy.distance.toFixed(1)} km
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t bg-gray-50">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSelect}
              disabled={!selectedId || loading}
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Sending...' : 'Send to Pharmacy'}
            </button>
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
};
```

### Step 3: Update Prescription Detail Page
**File**: `VitaNips-Frontend-Dev/src/pages/PrescriptionDetailPage.tsx` (or similar)

```typescript
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { PharmacySelectionModal } from '../components/PharmacySelectionModal';
import { forwardPrescriptionToPharmacy } from '../api/prescriptions';
import { toast } from 'react-hot-toast';

export const PrescriptionDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Fetch prescription data (use existing query)
  // const { data: prescription } = useQuery(...);

  const forwardMutation = useMutation({
    mutationFn: (pharmacyId: number) =>
      forwardPrescriptionToPharmacy(Number(id), { pharmacy_id: pharmacyId }),
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries(['prescriptions']);
      queryClient.invalidateQueries(['orders']);
      setIsModalOpen(false);
      // Optionally navigate to order detail
      navigate(`/orders/${data.order.id}`);
    },
    onError: (error: any) => {
      const message = error.response?.data?.error || 'Failed to forward prescription';
      toast.error(message);
    },
  });

  const handlePharmacySelect = (pharmacyId: number) => {
    forwardMutation.mutate(pharmacyId);
  };

  return (
    <div>
      {/* Existing prescription detail UI */}
      
      {/* Add "Send to Pharmacy" button */}
      <button
        onClick={() => setIsModalOpen(true)}
        className="mt-6 w-full bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition"
      >
        Send to Pharmacy
      </button>

      {/* Pharmacy Selection Modal */}
      <PharmacySelectionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSelect={handlePharmacySelect}
        loading={forwardMutation.isPending}
      />
    </div>
  );
};
```

### Step 4: Add Pharmacy API (if not exists)
**File**: `VitaNips-Frontend-Dev/src/api/pharmacy.ts`

```typescript
import api from './config';

export interface Pharmacy {
  id: number;
  name: string;
  address: string;
  phone_number: string;
  email: string;
  location?: {
    latitude: number;
    longitude: number;
  };
  is_active: boolean;
}

export interface PharmacyListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Pharmacy[];
}

export const getPharmacies = async (params?: {
  search?: string;
  latitude?: number;
  longitude?: number;
  radius?: number;
}): Promise<PharmacyListResponse> => {
  const response = await api.get('/pharmacy/pharmacies/', { params });
  return response.data;
};
```

---

## Testing Checklist

### Backend Tests
- [ ] Authenticated user can forward their own prescription
- [ ] User cannot forward someone else's prescription (404)
- [ ] Cannot forward if appointment not completed (400)
- [ ] Cannot forward if pharmacy is inactive (404)
- [ ] Cannot forward prescription without items (400)
- [ ] Cannot forward prescription twice to same pharmacy (409)
- [ ] Creates MedicationOrder with correct data
- [ ] Creates MedicationOrderItems from PrescriptionItems
- [ ] Creates user notification
- [ ] Logs success and errors

### Frontend Tests
- [ ] "Send to Pharmacy" button visible on prescription detail page
- [ ] Modal opens when button clicked
- [ ] Pharmacy list loads correctly
- [ ] Search filters pharmacies
- [ ] Can select a pharmacy
- [ ] Shows loading state during submission
- [ ] Shows success toast and navigates to order
- [ ] Shows error toast on failure
- [ ] Handles 409 conflict (already forwarded) gracefully

### Integration Tests
- [ ] Complete flow: view prescription → click button → select pharmacy → order created
- [ ] Order appears in "My Orders" page
- [ ] Pharmacy receives notification (if implemented)
- [ ] Cannot forward same prescription twice

---

## Security Considerations

1. **Authentication**: All endpoints require authentication
2. **Authorization**: Users can only forward their own prescriptions
3. **Validation**: All inputs validated (pharmacy_id, appointment status)
4. **Transaction Safety**: Atomic operations prevent data inconsistency
5. **Rate Limiting**: Consider adding rate limiting to prevent abuse

---

## Future Enhancements

1. **Pharmacy Notifications**
   - Email notification to pharmacy when order received
   - Template: `templates/emails/pharmacy_order_notification.html`

2. **Delivery Options**
   - Add delivery vs pickup choice
   - Delivery address selection

3. **Price Estimation**
   - Pharmacy provides price quotes
   - User confirms before finalizing

4. **Status Updates**
   - Real-time status updates (pending → confirmed → ready → delivered)
   - Push notifications for status changes

5. **Multiple Pharmacy Quotes**
   - Send to multiple pharmacies
   - Compare prices
   - Choose best option

6. **Prescription Image Upload**
   - Allow patients to upload prescription images
   - OCR to extract medication details

---

## API URL Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/doctors/prescriptions/<id>/forward/` | Forward prescription to pharmacy |
| GET | `/api/pharmacy/pharmacies/` | List available pharmacies |
| GET | `/api/pharmacy/orders/` | List user's medication orders |
| GET | `/api/pharmacy/orders/<id>/` | Get order details |

---

## Error Handling Guide

| Error Code | Meaning | User Action |
|------------|---------|-------------|
| 400 | Invalid request | Check if appointment is completed, prescription has items |
| 404 | Not found | Verify prescription exists and pharmacy is active |
| 409 | Already exists | View existing order instead |
| 500 | Server error | Retry or contact support |

---

## Deployment Notes

1. **Database Migrations**: No new migrations needed (models already exist)
2. **Environment Variables**: No new variables required
3. **Frontend Build**: Rebuild frontend after adding new components
4. **Testing**: Run full test suite before deploying
5. **Monitoring**: Monitor logs for prescription forwarding errors

---

## Support & Maintenance

- **Logs Location**: Check Django logs for prescription forwarding errors
- **Common Issues**:
  - "Appointment not completed" → Guide user to complete appointment first
  - "Pharmacy inactive" → Update pharmacy list
  - "Already forwarded" → Show existing order link
- **Contact**: Development team for API issues

---

**Last Updated**: January 2024  
**Status**: Backend ✅ Complete | Frontend ⚠️ Pending Implementation
