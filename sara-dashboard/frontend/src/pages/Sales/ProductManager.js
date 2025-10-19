import React, { useState, useEffect } from 'react';
import { PlusIcon, PencilIcon, TrashIcon, EyeIcon } from '@heroicons/react/24/outline';

const ProductManager = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'hotel',
    price: 0,
    currency: 'USD',
    features: [],
    faqs: [],
    targetAudience: {
      demographics: { ageRange: '', incomeLevel: '', location: '' },
      painPoints: [],
      buyingMotivations: []
    },
    competitorComparison: [],
    salesPitch: {
      opening: '',
      valueProposition: '',
      urgencyFactors: [],
      closingPhrases: []
    },
    isActive: true,
    priority: 1,
    tags: []
  });

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await fetch('/api/sales/products');
      const data = await response.json();
      if (data.success) {
        setProducts(data.data);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingProduct 
        ? `/api/sales/products/${editingProduct._id}`
        : '/api/sales/products';
      const method = editingProduct ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const result = await response.json();
      if (result.success) {
        fetchProducts();
        setShowModal(false);
        setEditingProduct(null);
        resetForm();
      }
    } catch (error) {
      console.error('Error saving product:', error);
    }
  };

  const handleDelete = async (productId) => {
    if (window.confirm('Are you sure you want to delete this product?')) {
      try {
        const response = await fetch(`/api/sales/products/${productId}`, {
          method: 'DELETE'
        });
        const result = await response.json();
        if (result.success) {
          fetchProducts();
        }
      } catch (error) {
        console.error('Error deleting product:', error);
      }
    }
  };

  const handleSetActive = async (productId) => {
    try {
      const response = await fetch(`/api/sales/products/${productId}/activate`, { method: 'PATCH' });
      const result = await response.json();
      if (result.success) {
        fetchProducts();
      }
    } catch (error) {
      console.error('Error setting active product:', error);
    }
  };

  const handleEdit = (product) => {
    setEditingProduct(product);
    setFormData(product);
    setShowModal(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      category: 'hotel',
      price: 0,
      currency: 'USD',
      features: [],
      faqs: [],
      targetAudience: {
        demographics: { ageRange: '', incomeLevel: '', location: '' },
        painPoints: [],
        buyingMotivations: []
      },
      competitorComparison: [],
      salesPitch: {
        opening: '',
        valueProposition: '',
        urgencyFactors: [],
        closingPhrases: []
      },
      isActive: true,
      priority: 1,
      tags: []
    });
  };

  const addFeature = () => {
    setFormData({
      ...formData,
      features: [...formData.features, { name: '', description: '', benefit: '' }]
    });
  };

  const updateFeature = (index, field, value) => {
    const newFeatures = [...formData.features];
    newFeatures[index][field] = value;
    setFormData({ ...formData, features: newFeatures });
  };

  const removeFeature = (index) => {
    const newFeatures = formData.features.filter((_, i) => i !== index);
    setFormData({ ...formData, features: newFeatures });
  };

  const addFAQ = () => {
    setFormData({
      ...formData,
      faqs: [...formData.faqs, { question: '', answer: '', language: 'en' }]
    });
  };

  const updateFAQ = (index, field, value) => {
    const newFAQs = [...formData.faqs];
    newFAQs[index][field] = value;
    setFormData({ ...formData, faqs: newFAQs });
  };

  const removeFAQ = (index) => {
    const newFAQs = formData.faqs.filter((_, i) => i !== index);
    setFormData({ ...formData, faqs: newFAQs });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Product Manager</h1>
        <button
          onClick={() => {
            resetForm();
            setEditingProduct(null);
            setShowModal(true);
          }}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <PlusIcon className="h-5 w-5" />
          Add Product
        </button>
      </div>

      {/* Products Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {products.map((product) => (
          <div key={product._id} className="bg-white rounded-lg shadow-md p-6 border">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-semibold text-gray-900">{product.name}</h3>
              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(product)}
                  className="text-blue-600 hover:text-blue-800"
                >
                  <PencilIcon className="h-5 w-5" />
                </button>
                <button
                  onClick={() => handleDelete(product._id)}
                  className="text-red-600 hover:text-red-800"
                >
                  <TrashIcon className="h-5 w-5" />
                </button>
                {!product.isActive && (
                  <button
                    onClick={() => handleSetActive(product._id)}
                    className="text-green-600 hover:text-green-800"
                    title="Set Active"
                  >
                    <EyeIcon className="h-5 w-5" />
                  </button>
                )}
              </div>
            </div>
            
            <p className="text-gray-600 mb-4">{product.description}</p>
            
            <div className="flex justify-between items-center mb-4">
              <span className="text-2xl font-bold text-green-600">
                {product.currency} {product.price}
              </span>
              <span className={`px-2 py-1 rounded-full text-xs ${
                product.isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {product.isActive ? 'Active' : 'Inactive'}
              </span>
            </div>
            
            <div className="text-sm text-gray-500">
              <p>Category: {product.category}</p>
              <p>Features: {product.features.length}</p>
              <p>FAQs: {product.faqs.length}</p>
              <p>Priority: {product.priority}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-6">
              {editingProduct ? 'Edit Product' : 'Add New Product'}
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Product Name
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Category
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="hotel">Hotel</option>
                    <option value="insurance">Insurance</option>
                    <option value="saas">SaaS</option>
                    <option value="real_estate">Real Estate</option>
                    <option value="ecommerce">E-commerce</option>
                    <option value="services">Services</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              {/* Pricing */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Price
                  </label>
                  <input
                    type="number"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Currency
                  </label>
                  <select
                    value={formData.currency}
                    onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="USD">USD</option>
                    <option value="INR">INR</option>
                    <option value="EUR">EUR</option>
                    <option value="GBP">GBP</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Priority
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Sales Pitch */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Opening Line (Hindi/English)
                </label>
                <textarea
                  value={formData.salesPitch.opening}
                  onChange={(e) => setFormData({ 
                    ...formData, 
                    salesPitch: { ...formData.salesPitch, opening: e.target.value }
                  })}
                  rows={2}
                  placeholder="Hello! Main aapko hotel booking service ke baare mein batana chahti hun..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Value Proposition
                </label>
                <textarea
                  value={formData.salesPitch.valueProposition}
                  onChange={(e) => setFormData({ 
                    ...formData, 
                    salesPitch: { ...formData.salesPitch, valueProposition: e.target.value }
                  })}
                  rows={2}
                  placeholder="We offer premium hotels at competitive prices with personalized service..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Features */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Features
                  </label>
                  <button
                    type="button"
                    onClick={addFeature}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    + Add Feature
                  </button>
                </div>
                {formData.features.map((feature, index) => (
                  <div key={index} className="grid grid-cols-1 md:grid-cols-3 gap-2 mb-2">
                    <input
                      type="text"
                      placeholder="Feature name"
                      value={feature.name}
                      onChange={(e) => updateFeature(index, 'name', e.target.value)}
                      className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <input
                      type="text"
                      placeholder="Description"
                      value={feature.description}
                      onChange={(e) => updateFeature(index, 'description', e.target.value)}
                      className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Benefit"
                        value={feature.benefit}
                        onChange={(e) => updateFeature(index, 'benefit', e.target.value)}
                        className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 flex-1"
                      />
                      <button
                        type="button"
                        onClick={() => removeFeature(index)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* FAQs */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    FAQs
                  </label>
                  <button
                    type="button"
                    onClick={addFAQ}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    + Add FAQ
                  </button>
                </div>
                {formData.faqs.map((faq, index) => (
                  <div key={index} className="mb-4 p-4 border border-gray-200 rounded-lg">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-2">
                      <input
                        type="text"
                        placeholder="Question"
                        value={faq.question}
                        onChange={(e) => updateFAQ(index, 'question', e.target.value)}
                        className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <select
                        value={faq.language}
                        onChange={(e) => updateFAQ(index, 'language', e.target.value)}
                        className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="en">English</option>
                        <option value="hi">Hindi</option>
                        <option value="mixed">Mixed</option>
                      </select>
                    </div>
                    <div className="flex gap-2">
                      <textarea
                        placeholder="Answer"
                        value={faq.answer}
                        onChange={(e) => updateFAQ(index, 'answer', e.target.value)}
                        rows={2}
                        className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 flex-1"
                      />
                      <button
                        type="button"
                        onClick={() => removeFAQ(index)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Status */}
              <div className="flex items-center gap-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.isActive}
                    onChange={(e) => setFormData({ ...formData, isActive: e.target.checked })}
                    className="mr-2"
                  />
                  Active Product
                </label>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  {editingProduct ? 'Update Product' : 'Create Product'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductManager;
